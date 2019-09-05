#!/usr/bin/python

# She Wore A Mirrored Mask ("SWAMM")
# Copyright 2014 Ben Lincoln
# http://www.beneaththewaves.net/
#

# This file is part of She Wore A Mirrored Mask ("SWAMM").

# She Wore A Mirrored Mask ("SWAMM") is free software: you can redistribute it and/or modify
# it under the terms of version 3 of the GNU General Public License as published by
# the Free Software Foundation.

# She Wore A Mirrored Mask ("SWAMM") is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with She Wore A Mirrored Mask ("SWAMM") (in the file LICENSE.txt).
# If not, see <http://www.gnu.org/licenses/>.
#

import argparse
import base64
import cgi
import copy
import datetime
import httplib
import logging
import math
import os
import random
import re
import socket
import subprocess
import sys
import time
import urllib

import libdeceitfulhttp
import libdeceitfulnetwork
import libfileio
import liblogging
import liboutput

__author__ = 'Ben Lincoln - http://www.beneaththewaves.net/'

# this is a bit of a hack, but doing it the right way with inspection is a lower priority than releasing a working version
# when adding new modules (which actually work for end users), be sure to add them to the results of this class' getModules function
class HTTPServerResponseProfileEnumerator:
	
	@staticmethod	
	def GetProfiles():
		profileList = []
		profileList.append(HTTPServerResponseProfileApacheCoyote11())
		profileList.append(HTTPServerResponseProfileApache2222Generic())
		profileList.append(HTTPServerResponseProfileApache2222Debian())
		profileList.append(HTTPServerResponseProfileApache2222Ubuntu())
		profileList.append(HTTPServerResponseProfileIIS50())
		profileList.append(HTTPServerResponseProfileIIS60())
		profileList.append(HTTPServerResponseProfileIIS70())
		profileList.append(HTTPServerResponseProfileIIS75())
		profileList.append(HTTPServerResponseProfileIIS80())

		return profileList
		
	def __init__(self):
		self.Profiles = HTTPServerResponseProfileEnumerator.GetProfiles()
		
	def GetProfileByUID(self, profileUID):
		for p in self.Profiles:
			if (p.UID == profileUID):
				return p
		return None

class HTTPServerResponseProfile:
	def __init__(self):
		self.UID = 'Default'
		self.Name = 'Default'
		self.Responses = {}
		self.ResponseVariables = {}
		self.ResponseVariables['%SERVERNAME%'] = 'Unspecified'
		self.GlobalHeaders = []
		self.GlobalHeaders.append(('Server', '%SERVERNAME%'))
		self.DefaultResponseCode = 404
		#self.UseResponseBodyFiles = False
		self.UseResponseBodyFiles = True
		self.Locale = 'en_US'
		self.DefaultLocale = 'en_US'
		self.ResponseBodyPath = libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/data/swamm/server_profiles/default/%LOCALE%/')
		
		# special responses
		self.OptionsResponse = libdeceitfulhttp.HTTPResponse()
		self.OptionsResponse.ResponseCode = 200
		self.OptionsResponse.ResponseReason = libdeceitfulhttp.HTTPResponse.GetHTTPResponseReasonFromCode(self.OptionsResponse.ResponseCode)
		self.OptionsResponse.AddOrReplaceHeader('Allow', 'GET,HEAD,POST,OPTIONS')
		
		#self.MethodNotAllowedResponse = libdeceitfulhttp.HTTPResponse()
		#self.MethodNotAllowedResponse.ResponseCode = 405
		#self.MethodNotAllowedResponse.ResponseReason = libdeceitfulhttp.HTTPResponse.GetHTTPResponseReasonFromCode(self.OptionsResponse.ResponseCode)
		#self.MethodNotAllowedResponse.AddOrReplaceHeader('Allow', 'GET,HEAD,POST,OPTIONS')
	
	def GetResponseBodyFile(self, fileName, multiLogger = None):
		result = ''
		if (self.UseResponseBodyFiles):
			fullPath = self.ResponseBodyPath + fileName
			if (multiLogger):
				multiLogger.debug('Attempting to obtain response body file "{0}"'.format(fullPath))
			try:
				fullPath = libfileio.LocalizedPath.GetLocalizedPath(fullPath, self.Locale, self.DefaultLocale)
				result = libfileio.FileReader.getFileAsString(fullPath)
				multiLogger.debug('Obtained response body file "{0}"'.format(fullPath))
			except Exception as e:
				errMsg = 'Error obtaining response body file "{0}" - {1} - {2}'.format(fullPath, str(type(e)), str(e.args))
				#print errMsg
				if (multiLogger):
					multiLogger.debug(errMsg)
				result = ''
		else:
			multiLogger.debug('The use of response body files is disabled, so an empty string will be used.'.format(fullPath))
		return result

	# this is not very extensive at the moment
	#def GetCharsetString(self, locale):
		#defaultString = 'iso-8859-1'
		#if (self.Locale == 'en_US'):
			#return 'iso-8859-1'
		#return defaultString
		
	def GetGenericResponse(self, responseCode):
		baseResponse = libdeceitfulhttp.HTTPResponse()
		baseResponse.ResponseCode = responseCode
		
	# can be overridden by sub-classes for mimicking servers that use a different format
	def GetServerDate(self):
		ts = datetime.datetime.utcnow()
		result = ts.strftime("%a, %d %b %Y %H:%M:%S GMT")
		#print 'Debug: current timestamp is {0}'.format(result) 
		return result

	def GetResponseTemplate(self, responseCode, multiLogger = None):
		result = libdeceitfulhttp.HTTPResponse()
		result.ResponseCode = responseCode
		result.ResponseReason = libdeceitfulhttp.HTTPResponse.GetHTTPResponseReasonFromCode(responseCode)
		result.Body = self.GetResponseBodyFile('body-{0}.txt'.format(responseCode), multiLogger)
		return result
		
	# this is intended to be overridden in many subclasses to implement quirks of specific platforms
	def GetServerSpecificFormattedLocalPath(self, url, multiLogger = None):
		result = url
		#if (multiLogger):
		#	multiLogger.debug('Formatting URL "{0}"'.format(result))
		#uc = libdeceitfulhttp.URLComponents.FromURL(httpRequest.URL, multiLogger)
		#result = '{0}?{1}'.format(uc.URIStem, uc.URLParameters)
		if (multiLogger):
			multiLogger.debug('Escaping result "{0}"'.format(result))
		#result = cgi.escape(result)
		result = urllib.unquote(result)
		result = result.replace('<', '&lt;')
		result = result.replace('>', '&gt;')
		result = result.replace('&60#;', '&lt;')
		result = result.replace('&62#;', '&gt;')
		if (multiLogger):
			multiLogger.debug('Returning final result "{0}"'.format(result))
		return result

	def GetResponseFromTemplate(self, templateResponse, httpRequest, clientLayer3Address, serverLayer3Address, responseCode, multiLogger = None):
		if (multiLogger):
			multiLogger.debug('Converting response to raw TCP message')
		responseRaw = templateResponse.ToRawTCPMessage()
		
		if (multiLogger):
			multiLogger.debug('Adding/updating response variables - server address')
		self.ResponseVariables['%SERVERIP%'] = serverLayer3Address.IPAddress
		self.ResponseVariables['%SERVERHOSTNAME%'] = serverLayer3Address.HostName
		self.ResponseVariables['%SERVERHOSTFQDN%'] = serverLayer3Address.HostFQDN
		self.ResponseVariables['%SERVERPORT%'] = str(serverLayer3Address.Port)

		if (multiLogger):
			multiLogger.debug('Adding/updating response variables - client address')
		self.ResponseVariables['%CLIENTIP%'] = clientLayer3Address.IPAddress
		self.ResponseVariables['%CLIENTHOSTNAME%'] = clientLayer3Address.HostName
		self.ResponseVariables['%CLIENTHOSTFQDN%'] = clientLayer3Address.HostFQDN
		self.ResponseVariables['%CLIENTPORT%'] = str(clientLayer3Address.Port)

		if (multiLogger):
			multiLogger.debug('Adding/updating response variables - HTTP request method')
		self.ResponseVariables['%REQUESTMETHOD%'] = httpRequest.HTTPMethod

		if (multiLogger):
			multiLogger.debug('Adding/updating response variables - URL/local path')
		self.ResponseVariables['%URLLOCAL%'] = self.GetServerSpecificFormattedLocalPath(httpRequest.URL, multiLogger)
		stemParamSeperatorIndex = httpRequest.URL.find('?')
		if (stemParamSeperatorIndex > -1):
			stem = liboutput.OutputUtils.Left(httpRequest.URL, stemParamSeperatorIndex)
			self.ResponseVariables['%URLLOCALSTEM%'] = self.GetServerSpecificFormattedLocalPath(stem, multiLogger)
		else:
			self.ResponseVariables['%URLLOCALSTEM%'] = self.ResponseVariables['%URLLOCAL%']
		
		if (responseRaw):
			if (multiLogger):
				multiLogger.debug('Actualizing template')
			responseRaw = liboutput.OutputUtils.ActualizeTemplate(responseRaw, self.ResponseVariables)
		else:
			if (multiLogger):
				multiLogger.error('Response template is empty - will not be actualized')
		if (multiLogger):
			multiLogger.debug('Converting raw TCP message back to an HTTP response:\n{0}'.format(responseRaw))
		result = libdeceitfulhttp.HTTPResponse.FromRawTCPMessage(responseRaw)
		if (multiLogger):
			multiLogger.debug('Returning result')
		return result
		
	def GetResponse(self, httpRequest, clientLayer3Address, serverLayer3Address, responseCode, multiLogger = None):
		if (multiLogger):
			multiLogger.debug('Getting response template')
			multiLogger.debug('Adding/updating response variables - server date')
		self.ResponseVariables['%SERVERDATE%'] = self.GetServerDate()
		
		baseResponse = libdeceitfulhttp.HTTPResponse()
		if (responseCode):
			baseResponse.ResponseCode = responseCode
		else:
			baseResponse.ResponseCode = 0
		if (multiLogger):
			if (baseResponse.ResponseCode == 0):
				multiLogger.warning('A response code was either not specified, or was set to code 0 - the default response code of {0} will be used'.format(self.DefaultResponseCode))
		if (baseResponse.ResponseCode == 0):
			baseResponse.ResponseCode = self.DefaultResponseCode
		if (multiLogger):
			multiLogger.debug('Using response code of {0}'.format(baseResponse.ResponseCode))
		if (baseResponse.ResponseCode in self.Responses.keys()):
			if (multiLogger):
				multiLogger.debug('Found a response in the server profile for response code {0}'.format(baseResponse.ResponseCode))
			baseResponse = self.Responses[baseResponse.ResponseCode]
			if (multiLogger):
				multiLogger.debug('Using predefined HTTP response for HTTP code {0}'.format(baseResponse.ResponseCode))
		else:
			if (multiLogger):
				multiLogger.debug('Did not find a response in the server profile for response code {0}'.format(baseResponse.ResponseCode))
			if (baseResponse.ResponseCode in self.Responses.keys()):
				if (multiLogger):
					multiLogger.debug('Found a response in the server profile for default response code {0}'.format(self.DefaultResponseCode))
				baseResponse = self.Responses[self.DefaultResponseCode]
				if (multiLogger):
					multiLogger.warning('The server response profile in use does not contain a specific response for HTTP code {0}, so the response for the default code ({1}) will be used instead'.format(baseResponse.ResponseCode, self.DefaultResponseCode))
			else:
				if (multiLogger):
					multiLogger.warning('The server response profile in use does not contain a specific response for HTTP code {0}, which is the default response code for the profile  - please contact the developer of the profile - a very generic response will be used'.format(baseResponse.ResponseCode, self.DefaultResponseCode))
		for gh in self.GlobalHeaders:
			multiLogger.debug('Adding global header "{0}"'.format(gh))
			if (len(gh) < 2):
				if (multiLogger):
					multiLogger.error('One of the global headers for this server profile is malformed (it is missing one or both of the header name and value) - please contact the developer of the profile - the problematic header will be ignored')
			else:
				baseResponse.AddOrReplaceHeader(gh[0], gh[1])
				if (multiLogger):
					multiLogger.debug('Added global header "{0}" with value "{1}"'.format(gh[0], gh[1]))
		if ((baseResponse.Body is None) or (baseResponse.Body == '')):
			baseResponse.Body = self.GetResponseBodyFile('body-{0}.txt'.format(baseResponse.ResponseCode), multiLogger)
			if (multiLogger):
				multiLogger.debug('Base response body is missing or blank, so the value from the template will be used')

		result = self.GetResponseFromTemplate(baseResponse, httpRequest, clientLayer3Address, serverLayer3Address, responseCode, multiLogger)
		return result
		
	def GetOptionsResponse(self, httpRequest, clientLayer3Address, serverLayer3Address, responseCode, multiLogger = None):
		result = self.GetResponseFromTemplate(self.OptionsResponse, httpRequest, clientLayer3Address, serverLayer3Address, responseCode, multiLogger)
		return result
		
	def GetMethodNotAllowedResponseResponse(self, httpRequest, clientLayer3Address, serverLayer3Address, multiLogger = None):
		result = self.GetResponse(httpRequest, clientLayer3Address, serverLayer3Address, 405, multiLogger)
		result.AddOrReplaceHeader('Allow', 'GET,HEAD,POST,OPTIONS')
		return result
		
class HTTPServerResponseProfileApache2(HTTPServerResponseProfile):
	def __init__(self):
		HTTPServerResponseProfile.__init__(self)
		self.UID = 'apache2generic'
		self.Name = 'Apache2Generic'
		self.ResponseVariables['%SERVERNAME%'] = 'Apache'
		self.GlobalHeaders.append(('Date', '%SERVERDATE%'))
		self.GlobalHeaders.append(('Vary', 'Accept-Encoding'))
		self.GlobalHeaders.append(('Keep-Alive', 'timeout=5, max=100'))
		#self.GlobalHeaders.append(('Connection', 'Keep-Alive'))
		self.ResponseBodyPath = libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/data/swamm/server_profiles/apache2/%LOCALE%/')
		self.AddResponses()
		
	def AddResponses(self):
		self.Responses = {}

		# HTTP 200/OK
		response200 = self.GetResponseTemplate(200)
		response200.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[200] = response200
		
		# HTTP 400/Bad Request
		response400 = self.GetResponseTemplate(400)
		response400.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[400] = response400

		# HTTP 401/Unauthorized
		response401 = self.GetResponseTemplate(401)
		response401.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[401] = response401
		
		# HTTP 403/Forbidden
		response403 = self.GetResponseTemplate(403)
		response403.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[403] = response403
		
		# HTTP 404/Not Found
		response404 = self.GetResponseTemplate(404)
		response404.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[404] = response404
		
		# HTTP 405/Method Not Allowed
		response405 = self.GetResponseTemplate(405)
		response405.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[405] = response405
		
		# HTTP 500/Internal Server Error
		response500 = self.GetResponseTemplate(500)
		response500.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[500] = response500
		
class HTTPServerResponseProfileApache2222Generic(HTTPServerResponseProfileApache2):
	def __init__(self):
		HTTPServerResponseProfileApache2.__init__(self)
		self.UID = 'apache2222'
		self.Name = 'Apache 2.2.22 (Generic)'
		self.ResponseVariables['%SERVERNAME%'] = 'Apache/2.2.22'
		
class HTTPServerResponseProfileApache2222Debian(HTTPServerResponseProfileApache2222Generic):
	def __init__(self):
		HTTPServerResponseProfileApache2222Generic.__init__(self)
		self.UID = 'apache2222debian'
		self.Name = 'Apache 2.2.22 (Debian)'
		self.ResponseVariables['%SERVERNAME%'] = 'Apache/2.2.22 (Debian)'
		
class HTTPServerResponseProfileApache2222Ubuntu(HTTPServerResponseProfileApache2222Generic):
	def __init__(self):
		HTTPServerResponseProfileApache2222Generic.__init__(self)
		self.UID = 'apache2222ubuntu'
		self.Name = 'Apache 2.2.22 (Ubuntu)'
		self.ResponseVariables['%SERVERNAME%'] = 'Apache/2.2.22 (Ubuntu)'
		
class HTTPServerResponseProfileIIS(HTTPServerResponseProfile):
	def __init__(self):
		HTTPServerResponseProfile.__init__(self)
		self.GlobalHeaders.append(('Date', '%SERVERDATE%'))
		
	def AddResponses(self):
		self.Responses = {}

		# HTTP 200/OK
		response200 = self.GetResponseTemplate(200)
		response200.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[200] = response200
		
		# HTTP 400/Bad Request
		response400 = self.GetResponseTemplate(400)
		response400.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[400] = response400

		# HTTP 401/Unauthorized
		response401 = self.GetResponseTemplate(401)
		response401.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[401] = response401
		
		# HTTP 403/Forbidden
		response403 = self.GetResponseTemplate(403)
		response403.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[403] = response403
		
		# HTTP 404/Not Found
		response404 = self.GetResponseTemplate(404)
		response404.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[404] = response404
		
		# HTTP 405/Method Not Allowed
		response405 = self.GetResponseTemplate(405)
		response405.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[405] = response405
		
		# HTTP 500/Internal Server Error
		response500 = self.GetResponseTemplate(500)
		response500.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[500] = response500

class HTTPServerResponseProfileIIS50(HTTPServerResponseProfileIIS):
	def __init__(self):
		HTTPServerResponseProfileIIS.__init__(self)
		self.UID = 'iis5'
		self.Name = 'IIS 5.0 (Windows Server 2000)'
		self.ResponseVariables['%SERVERNAME%'] = 'Microsoft-IIS/5.0'
		self.GlobalHeaders.append(('Connection', 'Close'))
		
		self.ResponseBodyPath = libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/data/swamm/server_profiles/iis50/%LOCALE%/')
		self.AddResponses()
		
class HTTPServerResponseProfileIIS60(HTTPServerResponseProfileIIS):
	def __init__(self):
		HTTPServerResponseProfileIIS.__init__(self)
		self.UID = 'iis6'
		self.Name = 'IIS 6.0 (Windows Server 2003)'
		self.ResponseVariables['%SERVERNAME%'] = 'Microsoft-IIS/6.0'
		self.GlobalHeaders.append(('X-Powered-By', 'ASP.NET'))
		
		self.ResponseBodyPath = libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/data/swamm/server_profiles/iis60/%LOCALE%/')
		self.AddResponses()
		
class HTTPServerResponseProfileIIS70(HTTPServerResponseProfileIIS):
	def __init__(self):
		HTTPServerResponseProfileIIS.__init__(self)
		self.UID = 'iis7'
		self.Name = 'IIS 7.0 (Windows Server 2008)'
		self.ResponseVariables['%SERVERNAME%'] = 'Microsoft-IIS/7.0'
		#self.GlobalHeaders.append(('X-Powered-By', 'ASP.NET'))
		
		self.ResponseBodyPath = libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/data/swamm/server_profiles/iis70/%LOCALE%/')
		self.AddResponses()

class HTTPServerResponseProfileIIS75(HTTPServerResponseProfileIIS):
	def __init__(self):
		HTTPServerResponseProfileIIS.__init__(self)
		self.UID = 'iis7.5'
		self.Name = 'IIS 7.5 (Windows Server 2008)'
		self.ResponseVariables['%SERVERNAME%'] = 'Microsoft-IIS/7.5'
		#self.GlobalHeaders.append(('X-Powered-By', 'ASP.NET'))
		
		self.ResponseBodyPath = libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/data/swamm/server_profiles/iis75/%LOCALE%/')
		self.AddResponses()
		
class HTTPServerResponseProfileIIS80(HTTPServerResponseProfileIIS):
	def __init__(self):
		HTTPServerResponseProfileIIS.__init__(self)
		self.UID = 'iis8'
		self.Name = 'IIS 8.0 (Windows Server 2012)'
		self.ResponseVariables['%SERVERNAME%'] = 'Microsoft-IIS/8.0'
		#self.GlobalHeaders.append(('X-Powered-By', 'ASP.NET'))
		
		self.ResponseBodyPath = libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/data/swamm/server_profiles/iis80/%LOCALE%/')
		self.AddResponses()
		
class HTTPServerResponseProfileApacheCoyote11(HTTPServerResponseProfile):
	def __init__(self):
		HTTPServerResponseProfile.__init__(self)
		self.UID = 'coyote1.1'
		self.Name = 'Apache Coyote 1.1'
		self.ResponseVariables['%SERVERNAME%'] = 'Apache-Coyote/1.1'
		self.GlobalHeaders.append(('Date', '%SERVERDATE%'))
		#self.GlobalHeaders.append(('Vary', 'Accept-Encoding'))
		#self.GlobalHeaders.append(('Keep-Alive', 'timeout=5, max=100'))
		#self.GlobalHeaders.append(('Connection', 'Keep-Alive'))
		self.ResponseBodyPath = libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/data/swamm/server_profiles/apachecoyote11/%LOCALE%/')
		self.AddResponses()
		self.DefaultResponseCode = 400
		
	def AddResponses(self):
		self.Responses = {}

		# HTTP 200/OK
		response200 = self.GetResponseTemplate(200)
		response200.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[200] = response200
		
		# HTTP 400/Bad Request
		response400 = self.GetResponseTemplate(400)
		response400.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[400] = response400

		# HTTP 401/Unauthorized
		response401 = self.GetResponseTemplate(401)
		response401.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[401] = response401
		
		# HTTP 403/Forbidden
		response403 = self.GetResponseTemplate(403)
		response403.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[403] = response403
		
		# HTTP 404/Not Found
		response404 = self.GetResponseTemplate(404)
		response404.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[404] = response404
		
		# HTTP 405/Method Not Allowed
		response405 = self.GetResponseTemplate(405)
		response405.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[405] = response405
		
		# HTTP 500/Internal Server Error
		response500 = self.GetResponseTemplate(500)
		response500.AddOrReplaceHeader('Content-Type', 'text/html')
		self.Responses[500] = response500