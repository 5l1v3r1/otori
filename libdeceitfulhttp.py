#!/usr/bin/python

# On The Outside, Reaching In ("OTORI")
# Copyright 2014 Ben Lincoln
# http://www.beneaththewaves.net/
#

# This file is part of On The Outside, Reaching In ("OTORI").

# On The Outside, Reaching In ("OTORI") is free software: you can redistribute it and/or modify
# it under the terms of version 3 of the GNU General Public License as published by
# the Free Software Foundation.

# On The Outside, Reaching In ("OTORI") is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with On The Outside, Reaching In ("OTORI") (in the file LICENSE.txt).  
# If not, see <http://www.gnu.org/licenses/>.

import cgi
import copy
import httplib
import re
import socket
import ssl
import sys
import thread
import time
import urllib

import libdeceitfulnetwork
import libfileio
import liblogging
import liboutput

# libDeceitfulHTTP
# components for building HTTP clients which attempt to disguise the true nature and/or activities of themselves or their associates


# Generates random (but somewhat-believable) XML tags
#	Intended for use in evading simple signature-based detection systems
#	(IE nearly every signature-based detection system)
class RandomXMLTagGenerator:
	
	def __init__(self):
		self.maxTagLength = 64
		self.numDictionaryEntriesPerResult = 4
		dictionaryFilePath = libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/data/american-english-lowercase-4-64.txt')
		self.rflg = libfileio.RandomFileLineGenerator(dictionaryFilePath)
		
	def generateTag(self):
		result = ''
		for i in range(0, self.numDictionaryEntriesPerResult):
			result = result + self.rflg.getRandomEntry()
		if (len(result) > self.maxTagLength):
			result = result[0:(maxTagLength - 1)]
		return result
		
# Generates random HTTP user-agents from a dictionary list
class RandomUserAgentGenerator:
	def __init__(self):
		dictionaryFilePath = libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/data/user-agents.txt')
		self.rflg = libfileio.RandomFileLineGenerator(dictionaryFilePath)
		
	def GenerateUserAgent(self):
		return self.rflg.getRandomEntry()

		

# Handlers applied to requests from clients before being sent to servers
#	Base request
#		Method
#		URL
#		HTTP version
#	HTTP headers
#		Accept			(can be used for fingerprinting/tracking)
#		Accept-Charset
#		Accept-Datetime		(note: "provisional")
#		Accept-Encoding
#		Accept-Language		(can be used for fingerprinting/tracking)
#		Authorization
#		Cache-Control
#		Connection
#		Content-Encoding
#		Content-Language
#		Content-Length
#		Content-Location
#		Content-MD5
#		Content-Range
#		Content-Type
#		Cookie			(can be used for fingerprinting/tracking)
#		Date
#		DNT			(deceitful requests should probably strip this out because they have nothing to hide!)
#		ETag			(can be used for fingerprinting/tracking)
#		Expect
#		From			(this should always be stripped or replaced for truly deceitful requests as it's supposed to contain an email address)
#		Front-End-Https
#		Host
#		If-Match
#		If-Modified-Since
#		If-None-Match
#		If-Range
#		If-Unmodified-Since
#		Max-Forwards
#		Origin			(part of cross-origin resource sharing - can probably alter/forge this to decrease client security)
#		Pragma
#		Proxy-Authorization
#		Proxy-Connection
#		Range
#		Referer
#		TE
#		Trailer
#		Transfer-Encoding
#		True-Client-IP		(note: nonstandard header used by Akamai)
#		Upgrade
#		User-Agent
#		Via			(for requests which reached the deceitful proxy via another proxy)
#		Warning
#		X-ATT-DeviceId		(should strip this out entirely or forge a value)
#		X-Wap-Profile		(should strip this out entirely or forge a value)
#		X-Forwarded-For
#		X-Forwarded-Proto
#		X-Requested-With


# Handlers applied to responses from servers before being sent back to clients
#	Base request
#		HTTP version
#		Status
#		Reason				(the human-readable text that corresponds to the Status code)
#	HTTP headers
#		Accept-Ranges
#		Access-Control-Allow-Origin	(part of cross-origin resource sharing - can probably alter/forge this to decrease client security)
#		Age
#		Allow
#		Alternate-Protocol		(note: nonstandard header or part of HTTP 2.0)
#		Cache-Control
#		Connection
#		Content-Disposition
#		Content-Encoding
#		Content-Language
#		Content-Length
#		Content-Location
#		Content-MD5
#		Content-Range
#		Content-Security-Policy	(note: nonstandard)
#		Content-Type
#		Date
#		ETag
#		Expires				(set to -1 or 0 to cause the client to consider it "already expired)
#		Last-Modified
#		Link
#		Location
#		P3P
#		Pragma
#		Proxy-Authenticate
#		Range?
#		Refresh
#		Retry-After
#		Server
#		Set-Cookie
#		Status
#		Strict-Transport-Security
#		Trailer
#		Transfer-Encoding
#		Upgrade
#		Vary
#		Via				(for responses which came from an upstream proxy)
#		Warning
#		WWW-Authenticate

#		X-AspNet-Version
#		X-Content-Security-Policy
#		X-Content-Type-Options
#		X-Frame-Options			(strip this out/modify it to weaken client-side protections)
#		X-Powered-By
#		X-Runtime
#		X-UA-Compatible
#		X-Version
#		X-WebKit-CSP
#		X-XSS-Protection		(strip this out/modify it to weaken client-side protections)


class URLComponents:
	def __init__(self):
		self.Protocol = ''
		self.UseSSL = False
		self.Host = ''
		self.Port = 0
		self.URIStem = ''
		self.URLParameters = ''
		self.URI = ''
		
	@staticmethod
	def FromURL(url, multiLogger = None):
		result = URLComponents()
		targetProtocol = ''
		useSSL = False
		targetHost = ''
		targetPort = 0
		targetURIStem = ''
		targetURIParams = ''
		targetURI = ''
		
		rexURL = re.compile(r"(?P<protocol>[^:]+)(://)(?P<layer3address>[^/]+)?(?P<uristem>[^?]*)($|\?)(?P<uriparams>.*)", flags=re.IGNORECASE)
		m = rexURL.match(url)
		if not (m):
			errMsg = 'The URL "' + url + '" does not appear to be valid.'
			if (multiLogger):
				multiLogger.error(errMsg)
			sys.exit(1)
		if (m.group('layer3address')):
			l3Address = m.group('layer3address')
			# IPv6 address
			rexLayer3Address = re.compile(r"(?P<host>\[[0-9A-F:]{1,256}\])?(?P<port>:[0-9]{1,5})", flags=re.IGNORECASE)
			mAddress = rexLayer3Address.match(l3Address)
			if ((mAddress) and (mAddress.group('host'))):
				if (multiLogger):
					multiLogger.debug('Found IPv6 host address/port in URL "' + url + '"')
				targetHost = m.group('host')
				if (multiLogger):
					multiLogger.debug('Found host "' + targetHost + '"')
				if (m.group('port')):
					try:
						p = m.group('port').replace(":", "")
						targetPort = int(p)
						if (multiLogger):
							multiLogger.debug('Found port "' + targetPort + '"')
					except:
						if (multiLogger):
							multiLogger.error('The URL "' + url + '" appears to contain a reference to a port which is not valid.')
			else:
				if (multiLogger):
					multiLogger.debug('Assuming URL "' + url + '" is DNS name or IPv4 address')
				l3Split = l3Address.split(':')
				targetHost = l3Split[0]
				if (multiLogger):
					multiLogger.debug('Found host "' + targetHost + '"')
				if (len(l3Split) > 1):
					try:
						if (multiLogger):
							multiLogger.debug('Trying to parse "{0}" as a port number'.format(l3Split[1]))
						targetPort = int(l3Split[1])
						if (multiLogger):
							multiLogger.debug('Found port "{0}"'.format(targetPort))
					except Exception as e:
						if (multiLogger):
							multiLogger.error('The URL "{0}" appears to contain a reference to a port which is not valid - exception: {1} - {2}'.format(url, str(type(e)), str(e.args)))
		if (m.group('protocol')):
			validProtocol = False
			if (multiLogger):
				multiLogger.debug('Trying to parse "{0}" as a protocol'.format(m.group('protocol')))
			targetProtocol = m.group('protocol').lower()
			if (multiLogger):
				multiLogger.debug('Found protocol "{0}"'.format(targetProtocol))
			if (targetProtocol == 'http'):
				validProtocol = True
				if (targetPort == 0):
					targetPort = 80
			if (targetProtocol == 'https'):
				validProtocol = True
				useSSL = True
				if (targetPort == 0):
					targetPort = 443
			if not (validProtocol):
				errMsg = 'The URL "' + url + '" contains an unsupported protocol ("' + targetProtocol + '")'
				if (multiLogger):
					multiLogger.critical(errMsg)
				#raise RequestError(errMsg)
				sys.exit(1)
		if (m.group('uristem')):
			if (multiLogger):
				multiLogger.debug('Trying to parse "{0}" as a URI stem'.format(m.group('uristem')))
			targetURIStem = m.group('uristem')
			if (m.group('uriparams')):
				if (multiLogger):
					multiLogger.debug('Trying to parse "{0}" as a set of URI parameters'.format(m.group('uriparams')))
				targetURIParams = m.group('uriparams')
				targetURI = targetURIStem + '?' + targetURIParams
			else:
				targetURI = targetURIStem
		result.Protocol = targetProtocol
		result.UseSSL = useSSL
		result.Host = targetHost
		result.Port = targetPort
		result.URIStem = targetURIStem
		result.URLParameters = targetURIParams
		result.URI = targetURI
		if (multiLogger):
			multiLogger.debug('Result:\nProtocol = "{0}"\nUse SSL = "{1}"\nHost = "{2}"\nPort = "{3}"\nProtocol = "{4}"\nURI Stem = "{5}"\nURI Parameters = "{6}"\nComplete URI = "{7}"'.format(result.Protocol, result.UseSSL, result.Host, result.Port, result.Protocol, result.URIStem, result.URLParameters, result.URI))
		return result
	
		
class HTTPHeader:
	def __init__(self):
		self.HeaderName = ''
		self.HeaderValue = ''
		
class HTTPMessage:
	def __init__(self, headers = None, body = None):
		# this needs to be reworked to use the HTTPHeader class above for maximum flexibility
		# like most of the HTTP stuff
		realBody = ''
		if (body != None):
			realBody = copy.deepcopy(body)
		realHeaders = []
		if (headers != None):
			realHeaders = copy.deepcopy(headers)
		self.Headers = []
		headerValueIsHashtable = False
		keys = []
		try:
			keys = realHeaders.keys()
			headerValueIsHashtable = True
		except:
			headerValueIsHashtable = False
		if (headerValueIsHashtable):
			for hkey in keys:
				#self.Headers[hkey] = headers[hkey]
				headerName = str(hkey)
				headerVal = str(realHeaders[hkey])
				self.Headers.append((headerName, headerVal))
				#print 'Debug: added header "{0}" with value "{1}" from hashtable'.format(headerName, headerVal)
		else:
			if (len(realHeaders) > 0):
				for i in range(0, len(realHeaders)):
					currentHeader = realHeaders[i]
					if (len(currentHeader) > 1):
						self.Headers.append((currentHeader[0], currentHeader[1]))
						#print 'Debug: added header "{0}" with value "{1}" from set of tuples'.format(currentHeader[0], currentHeader[1])
		self.MultiLogger = liblogging.MultiLogger()
		self.Body = realBody
		#print "Debug:::body"
		#print self.Body
		
	def AddOrReplaceHeader(self, headerName, headerValue):
		#self.Headers[headerName] = headerValue
		foundExistingHeader = False
		#print 'Debug: headerName = "{0}"'.format(headerName)
		#print 'Debug: headerValue = "{0}"'.format(headerValue)
		if (len(self.Headers) > 0):
			for i in range(0, len(self.Headers)):
				currentHeader = self.Headers[i]
				#print 'Debug: currentHeader = "{0}"'.format(currentHeader)
				if (len(currentHeader) > 1):
					#print 'Debug: currentHeader[0] = "{0}"'.format(currentHeader[0])
					#print 'Debug: currentHeader[1] = "{0}"'.format(currentHeader[1])
					if (currentHeader[0] == headerName):
						#currentHeader[1] = headerValue
						#self.Headers[i] = currentHeader
						#print 'Debug: updating existing header'.format(currentHeader[1])
						self.Headers[i] = (headerName, headerValue)
						foundExistingHeader = True
		if not (foundExistingHeader):
			self.Headers.append((headerName, headerValue))
		
	def GetHeaders(self):
		#result = []
		#for hkey in self.Headers.keys():
		#	result.append((hkey, self.Headers[hkey]))
		#return result
		return self.Headers
		
	def GetHeaderByName(self, headerName):
		if (len(self.Headers) > 0):
			for i in range(0, len(self.Headers)):
				currentHeader = self.Headers[i]
				if (len(currentHeader) > 1):
					if (currentHeader[0] == headerName):
						return currentHeader[1]
		return None
	
		
class HTTPRequest(HTTPMessage):
		
	def __init__(self, method = 'GET', url = '', httpVersion = 'HTTP/1.1', headers = None, body = None):
		realBody = ''
		if (body != None):
			realBody = copy.deepcopy(body)
		realHeaders = {}
		if (headers != None):
			realHeaders = copy.deepcopy(headers)
		HTTPMessage.__init__(self, realHeaders, realBody)
		self.HTTPMethod = method
		self.URL = url
		# note: this is not currently used very well
		self.HTTPVersion = httpVersion
		self.RequestTimeout = 60
		self.RawRequest = ''

	@staticmethod
	def FromExistingHTTPLibHTTPRequest(httpLibHTTPRequest):
		result = HTTPRequest()
		# do some stuff here if it becomes helpful
		
	@staticmethod
	def FromRawTCPMessage(tcpRequest):
		result = HTTPRequest()
		result.RawRequest = tcpRequest
		result.method = ''
		requestLines = tcpRequest.splitlines()
		if (requestLines):
			if (len(requestLines) > 0):
				# method/URI/HTTP version
				firstSpace = requestLines[0].find(' ')
				httpMethod = requestLines[0][0:(firstSpace + 1)]
				result.HTTPMethod = httpMethod.strip()
				#print 'method: "' + result.HTTPMethod + '"'
				remainder = requestLines[0][len(httpMethod):]
				#print 'remainder: "' + remainder + '"'
				rxHTTPVersion = r"(?P<version>HTTP/[0-9\\.]{1,8})($|[^0-9\\.])"
				rxHTTPVersion = r".* (?P<version>HTTP/[0-9\\.]{1,8})$"
				rx = re.compile(rxHTTPVersion, flags=re.IGNORECASE)
				m = rx.match(remainder)
				#print 'm: "' + str(m) + '"'
				if (m):
					result.HTTPVersion = m.group('version')
				else:
					#print 'Could not find HTTP version'
					result.HTTPVersion = ''
				#print 'HTTP version: "' + result.HTTPVersion + '"'
				
				remainder = remainder[0:(len(remainder) - len(result.HTTPVersion))]
				result.URL = remainder.strip()
				#print 'URI/URL: "' + result.URL + '"'

			if (len(requestLines) > 1):
				# headers
				currentLine = 1
				for lineNum in range(1,len(requestLines)):
					currentLine = lineNum
					if (requestLines[lineNum].strip() == ''):
						break
					clSplit = requestLines[lineNum].split(':')
					headerName = clSplit[0].strip()
					headerValue = ''
					if (len(clSplit) > 1):
						headerValue = clSplit[1].strip()
					result.AddOrReplaceHeader(headerName, headerValue)
					#print 'added header "' + headerName + '" with value "' + headerValue + '"'
				if (currentLine < len(requestLines)):
					for lineNum in range(currentLine, len(requestLines)):
						result.Body = result.Body + requestLines[lineNum] + '\n'
						#result.Body = result.Body + requestLines[lineNum] + '\r\n'
				#print 'result body "' + result.Body + '"'
		return result
		
	def ToRawTCPMessage(self):
		result = self.HTTPMethod
		result = result + ' ' + self.URL
		if ((self.HTTPVersion) and (self.HTTPVersion != '')):
			result = result + ' ' + self.HTTPVersion
		result = result + '\r\n'
		headerString = ''
		#for h in self.Headers.keys():
			#headerString = headerString + h.strip() + ': ' + self.Headers[h].strip() + '\n'
		for h in self.Headers:
			if (len(h) > 1):
				headerName = h[0]
				headerVal = h[1]
				if (self.MultiLogger):
					self.MultiLogger.debug('Adding header "{0}" with value "{1}"'.format(headerName, headerVal))
				#headerString = headerString + h.strip() + ': ' + self.Headers[h].strip() + '\n'
				headerString = headerString + '{0}: {1}\r\n'.format(headerName, headerVal)
			else:
				if (self.MultiLogger):
					self.MultiLogger.error('Bad header: "{0}"'.format(h))
		bodyString = self.Body
		bodyString = bodyString.replace('\n', '\r\n')
		bodyString = bodyString.replace('\r\r\n', '\r\n')
		result = result + headerString + '\r\n' + bodyString + '\r\n'
		if (self.MultiLogger):
			self.MultiLogger.debug('Generated raw TCP message request:\n' + result + '\n')
		
		return result
		
	def SendRequest(self):
		# parse the target URL into a host, port, and whether SSL is used or not
		useSSL = False
		targetHost = ''
		targetPort = 0
		targetURI = ''
		
		uc = URLComponents.FromURL(self.URL, self.MultiLogger)
		
		useSSL = uc.UseSSL
		targetHost = uc.Host
		targetPort = uc.Port
		targetURI = uc.URI
				
				
		hc = httplib.HTTPConnection(targetHost, targetPort, timeout = self.RequestTimeout)
		if (useSSL):
			hc = httplib.HTTPSConnection(targetHost, targetPort, timeout = self.RequestTimeout)
		
		result = HTTPResponse()

		if (self.MultiLogger):
			self.MultiLogger.debug('Sending request: ' + self.HTTPMethod + ' ' + targetURI)

		clHeaderOriginal = self.GetHeaderByName('Content-Length')
		contentLength = 0
		if (self.Body):
			#self.MultiLogger.warning('self.Body: "{0}"'.format(self.Body))
			#print 'self.Body: "{0}"'.format(self.Body)
			contentLength = len(self.Body)
		self.AddOrReplaceHeader('Content-Length', '{0}'.format(contentLength))
		clHeaderRevised = self.GetHeaderByName('Content-Length')
		if not (clHeaderOriginal):
			self.MultiLogger.debug('Added missing Content-Length header with value "{0}"'.format(contentLength))
		else:
			if (clHeaderOriginal != clHeaderRevised):
				self.MultiLogger.debug('Updated incorrect Content-Length header from "{0}" to "{1}"'.format(clHeaderOriginal, clHeaderRevised))
			else:
				self.MultiLogger.debug('Request already contained the correct Content-Length header ("{0}") - no update was required'.format(clHeaderOriginal))
			
		headerString = ''
		#for h in self.Headers.keys():
			#headerString = headerString + h.strip() + ': ' + self.Headers[h].strip() + '\n'
		# hack to get things working for now
		# until I completely replace the httplib requests with raw TCP requests that support multiple headers with the same name
		httplibHeaders = {}
		foundHostHeader = False
		for h in self.Headers:
			hLen = len([h])
			#print 'Debug: found header "{0}" with length "{1}" (step 1)'.format(h, hLen)
			if (len(h) > 0):
				hLen = len(h[1])
			#print 'Debug: found header "{0}" with length "{1}" (step 2)'.format(h, hLen)
			if (hLen > 1):
				headerName = h[0].strip()
				headerVal = h[1].strip()
				#print 'Debug: found header "{0}" with value "{1}"'.format(headerName, headerVal)
				headerString = headerString + '{0}: {1}\r\n'.format(headerName, headerVal)
				httplibHeaders[headerName] = headerVal
				if (headerName == 'Host'):
					foundHostHeader = True
		if not (foundHostHeader):
			missingHost = '{0}:{1}'.format(targetHost, targetPort)
			if (self.MultiLogger):
				self.MultiLogger.debug('Adding missing Host header "{0}"'.format(missingHost))
			headerName = 'Host'
			#headerString = headerString + '{0}: {1}\n'.format(headerName, targetHost)
			headerString = headerString + '{0}: {1}\r\n'.format(headerName, missingHost)
			httplibHeaders[headerName] = missingHost
			
		if (self.MultiLogger):
			self.MultiLogger.debug('Request headers:\n' + headerString + '\n\n')
			if (self.Body):
				self.MultiLogger.debug('Request body:\n' + self.Body + '\n\n')
		
		try:
			self.MultiLogger.debug('Connecting')
			hc.connect()
			self.MultiLogger.debug('Sending request with method "{0}", target URI "{1}", headers:\n{2}\n, body:\n{3}'.format(self.HTTPMethod, targetURI, self.Headers, self.Body))

			#request = hc.request(self.HTTPMethod, targetURI, self.Body, self.Headers)
			request = hc.request(self.HTTPMethod, targetURI, self.Body, httplibHeaders)
		
			#if (self.Body):
				#self.MultiLogger.debug('Sending request body')
				#hc.send(self.Body)
			#else:
				#self.MultiLogger.debug('No request body - sending empty string')
				#hc.send('')
			#hc.send('')
			hc.send('')

			self.MultiLogger.debug('Getting response')
			response = hc.getresponse()
			
			self.MultiLogger.debug('Converting response')
			result = HTTPResponse.FromExistingHTTPLibHTTPResponse(response)
		
			#result.Body = response.read()
			self.MultiLogger.debug('Closing connection')
			hc.close
		except Exception as e:
			if (self.MultiLogger):
				self.MultiLogger.error('Error sending request: ' + self.HTTPMethod + ' ' + targetURI)
				self.MultiLogger.error('Exception: ' + str(type(e)) + ' - ' + str(e.args))
			#result.NetworkLevelResponse.Error = True
			#if (len(e.args) > 0):
				#result.NetworkLevelResponse.ResponseCode = e.args[0]
			#if (len(e.args) > 1):
				#result.NetworkLevelResponse.Message = e.args[1]
			result.NetworkLevelResponse.SetValuesFromExceptionArgs(e.args)

		if (self.MultiLogger):
			self.MultiLogger.debug('Response:\n' + result.HTTPVersion + ' ' + str(result.ResponseCode) + ' ' + result.ResponseReason)
		headerString = ''
		#for h in result.Headers.keys():
			#headerString = headerString + h.strip() + ': ' + result.Headers[h].strip() + '\n'
		for h in result.Headers:
			if (len(h) > 0):
				headerString = headerString + h[0].strip()
				if (len(h) > 1):
					headerString = headerString + ': '
					for i in range(1, len(h)):
						headerString = headerString + h[i]
						if (i < (len(h) - 1)):
							headerString = headerString + '; '
				headerString = headerString + '\r\n'
		if (self.MultiLogger):
			self.MultiLogger.debug('Response headers:\n' + headerString + '\n\n')
			self.MultiLogger.debug('Response body:\n' + result.Body + '\n\n')
			self.MultiLogger.debug('Response generated a network-level error: ' + str(result.NetworkLevelResponse.Error) + '\n')
			if (result.NetworkLevelResponse.Error):
				self.MultiLogger.debug('Network-level response code: ' + str(result.NetworkLevelResponse.ResponseCode) + '\n')
				self.MultiLogger.debug('Network-level message: ' + str(result.NetworkLevelResponse.Message) + '\n')
		
		return result
		
class HTTPResponse(HTTPMessage):
	def __init__(self, httpVersion = 'HTTP/1.1', responseCode = 0, responseReason = '', headers = {}, body = ''):
		HTTPMessage.__init__(self, headers, body)
		self.MultiLogger = None
		self.HTTPVersion = httpVersion
		self.ResponseCode = responseCode
		self.ResponseReason = responseReason
		self.NetworkLevelResponse = libdeceitfulnetwork.NetworkLevelResponse()
		self.DefaultHTTPResponseCode = 404
		self.RawResponse = ''

	@staticmethod
	def FromExistingHTTPLibHTTPResponse(httpLibHTTPResponse):
		httpVersion = ''
		foundVersion = False
		if (httpLibHTTPResponse.version == 10):
			httpVersion = 'HTTP/1.0'
			foundVersion = True
		if (httpLibHTTPResponse.version == 11):
			httpVersion = 'HTTP/1.1'
			foundVersion = True
		if not (foundVersion):
			print 'Unfinished code: unknown HTTP version: "' + str(httpLibHTTPResponse.version) + '"'
		headers = httpLibHTTPResponse.getheaders()
		#print 'Debug: headers: {0}'.format(headers)
		result = HTTPResponse(httpVersion, httpLibHTTPResponse.status, httpLibHTTPResponse.reason, headers, httpLibHTTPResponse.read())
		return result
		
	@staticmethod
	def GetHTTPResponseReasonFromCode(responseCode):
		if (responseCode == 100):
			return "Continue"
		if (responseCode == 101):
			return "Switching Protocols"
		if (responseCode == 200):
			return "OK"
		if (responseCode == 201):
			return "Created"
		if (responseCode == 202):
			return "Accepted"
		if (responseCode == 203):
			return "Non-Authoritative Information"
		if (responseCode == 204):
			return "No Content"
		if (responseCode == 205):
			return "Reset Content"
		if (responseCode == 206):
			return "Partial Content"
		if (responseCode == 300):
			return "Multiple Choices"
		if (responseCode == 301):
			return "Moved Permanently"
		if (responseCode == 302):
			return "Found"
		if (responseCode == 303):
			return "See Other"
		if (responseCode == 304):
			return "Not Modified"
		if (responseCode == 305):
			return "Use Proxy"
		#if (responseCode == 306):
			#return "(Unused)"
		if (responseCode == 307):
			return "Temporary Redirect"
		if (responseCode == 400):
			return "Bad Request"
		if (responseCode == 401):
			return "Unauthorized"
		if (responseCode == 402):
			return "Payment Required"
		if (responseCode == 403):
			return "Forbidden"
		if (responseCode == 404):
			return "Not Found"
		if (responseCode == 405):
			return "Method Not Allowed"
		if (responseCode == 406):
			return "Not Acceptable"
		if (responseCode == 407):
			return "Proxy Authentication Required"
		if (responseCode == 408):
			return "Request Timeout"
		if (responseCode == 409):
			return "Conflict"
		if (responseCode == 410):
			return "Gone"
		if (responseCode == 411):
			return "Length Required"
		if (responseCode == 412):
			return "Precondition Failed"
		if (responseCode == 413):
			return "Request Entity Too Large"
		if (responseCode == 414):
			return "Request-URI Too Long"
		if (responseCode == 415):
			return "Unsupported Media Type"
		if (responseCode == 416):
			return "Requested Range Not Satisfiable"
		if (responseCode == 417):
			return "Expectation Failed"
		if (responseCode == 500):
			return "Internal Server Error"
		if (responseCode == 501):
			return "Not Implemented"
		if (responseCode == 502):
			return "Bad Gateway"
		if (responseCode == 503):
			return "Service Unavailable"
		if (responseCode == 504):
			return "Gateway Timeout"
		if (responseCode == 505):
			return "HTTP Version Not Supported"
		return "Unknown"

	@staticmethod
	def FromRawTCPMessage(tcpMessage):
		result = HTTPResponse()
		result.RawResponse = tcpMessage
		splitPoint = tcpMessage.find('\r\n\r\n')
		#print 'Debug: length = {0}'.format(len(tcpMessage))
		#print 'Debug: split point = {0}'.format(splitPoint)
		messageHeader = tcpMessage
		messageBody = ''
		if (splitPoint > 0):
			#print 'Body found'
			#print 'Capturing header'
			messageHeader = liboutput.OutputUtils.Left(tcpMessage, splitPoint)
			#print 'Capturing body'
			messageBody = liboutput.OutputUtils.RightLess(tcpMessage, splitPoint)
			#print 'Debug: message header block:\n{0}'.format(messageHeader)
			#print 'Debug: message body block:\n{0}'.format(messageBody)
		#messageLines = tcpMessage.splitlines()
		messageLines = messageHeader.splitlines()
		if (messageLines):
			if (len(messageLines) > 0):
				# HTTP version
				remainder = messageLines[0]
				#rxHTTPVersion = r"(?P<version>HTTP/[0-9\\.]{1,8})($|[^0-9\\.])"
				rxHTTPVersion = r"(?P<version>HTTP/[0-9\\.]{1,8})([^0-9\\.])"
				#rxHTTPVersion = r".* (?P<version>HTTP/[0-9\\.]{1,8})$"
				rx = re.compile(rxHTTPVersion, flags=re.IGNORECASE)
				m = rx.match(remainder)
				#print 'm: "' + str(m) + '"'
				if (m):
					result.HTTPVersion = m.group('version')
				else:
					#print 'Could not find HTTP version'
					result.HTTPVersion = ''
				#print 'HTTP version: "' + result.HTTPVersion + '"'
				
				remainder = remainder.replace(result.HTTPVersion, '').strip()
				#print 'remainder: "{0}"'.format(remainder)
				
				# HTTP response code
				rxHTTPResponseCode = r"(?P<responsecode>[0-9]{1,8})([^0-9])"
				rx = re.compile(rxHTTPResponseCode, flags=re.IGNORECASE)
				m = rx.match(remainder)
				if (m):
					rc = m.group('responsecode')
					try:
						result.ResponseCode = int(m.group('responsecode'))
					except Exception as e:
						#print 'Could not convert "{0}" to an HTTP response code'.format(rc)
						dummy = 1
				else:
					#print 'Could not find HTTP response code'
					dummy = 1
				#print 'HTTP response code: {0}'.format(str(result.ResponseCode))
				
				remainder = remainder.replace(str(result.ResponseCode), '')
				#print 'remainder: "{0}"'.format(remainder)
				
				result.ResponseReason = remainder.strip()
				#print 'ResponseReason: "{0}"'.format(result.ResponseReason)

			if (len(messageLines) > 1):
				# headers
				#currentLine = 1
				for lineNum in range(1,len(messageLines)):
					#currentLine = lineNum
					#print 'Line number {0} of {1}'.format(lineNum, (len(messageLines) - 1))
					if (messageLines[lineNum].strip() == ''):
						break
					#clSplit = messageLines[lineNum].split(':')
					#headerName = clSplit[0].strip()
					#headerValue = ''
					#if (len(clSplit) > 1):
						#headerValue = clSplit[1].strip()
					colonIndex = messageLines[lineNum].find(':')
					if (colonIndex > -1):
						headerName = liboutput.OutputUtils.Left(messageLines[lineNum], colonIndex)
						headerValue = liboutput.OutputUtils.RightLess(messageLines[lineNum], len(headerName) + 1).strip()
						result.AddOrReplaceHeader(headerName, headerValue)
					#print 'added header "' + headerName + '" with value "' + headerValue + '"'
				#if (currentLine < len(messageLines)):
					#for lineNum in range(currentLine, len(messageLines)):
						#result.Body = result.Body + messageLines[lineNum] + '\n'
				#print 'result body "' + result.Body + '"'
		if (messageBody != ''):
			#print 'adding body'
			result.Body = messageBody
			donePreTrimming = False
			#while (liboutput.OutputUtils.Left(result.Body, 1) == '\n'):
				#result.Body = liboutput.OutputUtils.RightLess(result.Body, 1)
			if (result.Body.strip() == ''):
				donePreTrimming = True
			while not (donePreTrimming):
				if not (donePreTrimming):
					if (len(result.Body) > 1):
						if ((liboutput.OutputUtils.Left(result.Body, 1) != '\n') and (liboutput.OutputUtils.Left(result.Body, 1) != '\r')):
							donePreTrimming = True
						else:
							result.Body = liboutput.OutputUtils.RightLess(result.Body, 1)
					else:
						donePreTrimming = True
			#print 'result body "' + result.Body + '"'
		return result
		
	def ToRawTCPMessage(self):
		if (self.MultiLogger):
			self.MultiLogger.debug('Building raw TCP message')
		result = self.HTTPVersion
		#responseCode = self.ResponseCode
		#responseReason = HTTPResponse.GetHTTPResponseReasonFromCode(responseCode)
		#if (responseReason == "Unknown"):
			#responseCode = self.DefaultHTTPResponseCode
			#responseReason = HTTPResponse.GetHTTPResponseReasonFromCode(responseCode)
		#result = result + ' {0} {1}\n'.format(self.ResponseCode, responseReason)self.ResponseReason
		result = result + ' {0} {1}\r\n'.format(self.ResponseCode, self.ResponseReason)
		headerString = ''
		#for h in self.Headers.keys():
			##headerString = headerString + h.strip() + ': ' + self.Headers[h].strip() + '\n'
			#headerLine = '{0}: {1}\n'.format(h, self.Headers[h])
			#if (self.MultiLogger):
				#self.MultiLogger.debug('Added header line: "{0}"'.format(headerLine.strip()))
			#headerString = headerString + headerLine
		for h in self.Headers:
			if (len(h) > 1):
				headerName = h[0]
				headerVal = h[1]
				if (self.MultiLogger):
					self.MultiLogger.debug('Adding header "{0}" with value "{1}"'.format(headerName, headerVal))
				headerString = headerString + '{0}: {1}\r\n'.format(headerName, headerVal)
			else:
				if (self.MultiLogger):
					self.MultiLogger.error('Bad header: "{0}"'.format(h))
		#result = result + headerString + '\n' + self.Body + '\n'
		bodyString = self.Body
		bodyString = bodyString.replace('\n', '\r\n')
		bodyString = bodyString.replace('\r\r\n', '\r\n')
		donePostTrimming = False
		while not (donePostTrimming):
			if not (donePostTrimming):
				if (len(headerString) > 1):
					if ((liboutput.OutputUtils.Right(headerString, 1) != '\n') and (liboutput.OutputUtils.Right(headerString, 1) != '\r')):
						donePostTrimming = True
					else:
						headerString = liboutput.OutputUtils.LeftLess(headerString, 1)
				else:
					donePostTrimming = True

		result = result + headerString + '\r\n\r\n' + bodyString
		if (self.MultiLogger):
			self.MultiLogger.debug('Generated raw TCP message response:\n' + result + '\n')
		
		return result

class HTTPMessageHandlerResponse:
	
	RESPONSE_PROCEED_WITH_OTHER_HANDLERS = 0
	RESPONSE_NO_FURTHER_PROCESSING = 1
	
	def __init__(self):
		self.Request = HTTPRequest()
		self.Response = HTTPResponse()
		self.ResponseCode = RESPONSE_PROCEED_WITH_OTHER_HANDLERS
		self.MessageModified = False
		
class HTTPMessageHandler:
	def __init__(self, multiLogger):
		self.MultiLogger = multiLogger

	def HandleMessage(self, httpRequest, httpResponse):
		self.MultiLogger.debug('Base/null HTTPMessageHandler instance received HTTP message')
		result = HTTPMessageHandlerResponse()
		result.Request = httpRequest
		result.Response = httpResponse
		return result
		
class HTTPRequestHandler(HTTPMessageHandler):
	def __init__(self, multiLogger):
		HTTPMessageHandler.__init__(self, multiLogger)
		
class HTTPResponseHandler(HTTPMessageHandler):
	def __init__(self, multiLogger):
		HTTPMessageHandler.__init__(self, multiLogger)

#class HTTPRequestHandlerSWAMM(HTTPRequestHandler):
	#def __init__(self, multiLogger, parentServer):
		#HTTPRequestHandler.__init__(self, multiLogger)
		#self.ParentServer = parentServer

	#def HandleMessage(self, httpRequest, httpResponse):

class HTTPHeaderHandler:
	def __init__(self, multiLogger):
		self.MultiLogger = multiLogger
		self.Header = HTTPHeader()
		self.Header.HeaderName = ''
		self.Header.HeaderValue = ''
		self.IgnoreNonMatchingHeaderNames = True
		
	def HandleHeader(self, header):
		if (self.IgnoreNonMatchingHeaderNames):
			if not (header.HeaderName == self.Header.HeaderName):
				return header
		return self.HandleHeaderInner(copy.deepcopy(header))

	# this is the method that should be overridden in subclasses
	# it's split out to avoid having to handle the ignore-non-matching-names logic and deep copy in every subclass
	def HandleHeaderInner(self, header):
		result = header
		return result


		
class DeceitfulHTTPClient:
	def __init__(self, multiLogger = None):
		self.MultiLogger = multiLogger
		self.UpstreamProxies = []
		self.RequestTimeout = 60
		self.HTTPVersion = 'HTTP/1.1'
		
		# HTTP version handler (always send same version, etc.)
		# Headers

		#	
		# User-Agent spoofing and/or modification (stripping distinctive data, etc.)
		# 
		# Accept-Language header modification (stripping distinctive data, etc.)
		# 
		# X-Forwarded-For spoofing
		# True-Client-IP header spoofing
		# Generate false Referer header based on the current URL being requested
		# Attempt to prevent cached responses from being returned
		# List of upstream proxies (and associated configuratin information) to use
		# Module which determines which upstream proxy will be used

	def BuildRequest(self, method, url, headers, body):
		result = HTTPRequest(method, url, self.HTTPVersion, headers, body)
		result.MultiLogger = self.MultiLogger
		result.RequestTimeout = self.RequestTimeout
		# to do: all of the cool handler stuff based on the base DeceitfulHTTPClient that doesn't exist yet
		return result
		
		
	def SendRequest(self, httpRequest):
		# to do: any modifications to the request based on the other cool stuff that doesn't exist yet
		result = httpRequest.SendRequest()
		# to do: any modifications to the response based on the other cool stuff that doesn't exist yet
		return result

class DeceitfulHTTPServerWorker:
	WORKERSTATE_STOPPED = 0
	WORKERSTATE_RUNNING = 1
	WORKERSTATE_STARTING = 2
	WORKERSTATE_STOPPING = 4
	WORKERSTATE_FORCESTOP = 8
	WORKERSTATE_ERROR = 16
	
	def __init__(self, parentServer, serverSocket, clientSocket, serverAddressForClient):
		self.ParentServer = parentServer
		self.ServerSocket = serverSocket
		self.ClientSocket = clientSocket
		self.ServerAddressForClient = serverAddressForClient
		self.State = DeceitfulHTTPServerWorker.WORKERSTATE_STOPPED
		self.LogDebug('Worker instantiated')
		self.RequestBufferCheckLimit = 20
		self.RequestBufferWaitLength = 0.001
		#self.RequestBufferCheckLimit = 10
		#self.RequestBufferWaitLength = 0.005
		self.MaxSocketErrors = 30

	def GetLogLinePrefix(self, serverSocket, clientSocket):
		result = self.ParentServer.GetLogLinePrefix(serverSocket)
		if ((clientSocket) and (clientSocket.Layer3Address)):
			result = result + '<=> ' + clientSocket.Layer3Address.GetFormattedName(self.ParentServer.UseFQDNsWhereAvailable)
		return result

	def LogDebug(self, message):
		self.ParentServer.MultiLogger.debug(self.GetLogLinePrefix(self.ServerSocket, self.ClientSocket) + ' - ' + message)

	def LogInfo(self, message):
		self.ParentServer.MultiLogger.info(self.GetLogLinePrefix(self.ServerSocket, self.ClientSocket) + ' - ' + message)

	def LogWarning(self, message):
		self.ParentServer.MultiLogger.warning(self.GetLogLinePrefix(self.ServerSocket, self.ClientSocket) + ' - ' + message)

	def LogError(self, message):
		self.ParentServer.MultiLogger.error(self.GetLogLinePrefix(self.ServerSocket, self.ClientSocket) + ' - ' + message)
		
	def LogCritical(self, message):
		self.ParentServer.MultiLogger.critical(self.GetLogLinePrefix(self.ServerSocket, self.ClientSocket) + ' - ' + message)
		
	def Run(self, dummyVariable):
		self.State = DeceitfulHTTPServerWorker.WORKERSTATE_RUNNING
		numErrors = 0
		self.LogInfo('Worker waiting for client message')
		currentMessage = ''
		readCount = 0
		transmissionStarted = False
		while (self.State == DeceitfulHTTPServerWorker.WORKERSTATE_RUNNING):
			try:
				request = ''
				gotData = False
				try:
					request = self.ClientSocket.Socket.recv(self.ParentServer.BufferSize)
					gotData = True
				except Exception as e:
					gotData = False
				
				if (gotData):
					transmissionStarted = True
					# reset read counter
					readCount = 0
					#if (currentMessage != ''):
					#	currentMessage = currentMessage + '\n'
					#currentMessage = currentMessage + request + '\n'
					currentMessage = currentMessage + request
					self.LogDebug('Message received')
					if (request):
						if (request == ''):
							self.LogDebug('Client is done sending - sent empty string')
							self.State = DeceitfulHTTPServerWorker.WORKERSTATE_STOPPING
							break
						try:
							self.LogDebug('Client sent message: \n{0}'.format(request))
						except Exception as e:
							if (e is socket.timeout):
								self.LogDebug('Client is done sending - socket timeout')
							else:
								self.LogError('Error logging message from client - {0} - {1}'.format(str(type(e)), str(e.args)))
								numErrors = numErrors + 1
					else:
						self.LogInfo('Client closed connection')
						break
				else:
					x = 1
			except Exception as e:
				self.LogError('Error reading message from client - {0} - {1}'.format(str(type(e)), str(e.args)))
				numErrors = numErrors + 1
			if (numErrors >= self.MaxSocketErrors):
				self.LogError('{0} errors have occurred in this thread (max: {1}) - worker will now shut down'.format(numErrors, self.MaxSocketErrors))
				self.State = DeceitfulHTTPServerWorker.WORKERSTATE_STOPPING
			if (transmissionStarted):
				readCount = readCount + 1
				if (readCount > self.RequestBufferCheckLimit):
					self.LogDebug('Exceeded maximum wait for more data')
					self.State = DeceitfulHTTPServerWorker.WORKERSTATE_STOPPING
					break
			time.sleep(self.RequestBufferWaitLength)
		if (currentMessage.strip() != ''):
			try:
				self.LogDebug('Complete message: \n{0}'.format(currentMessage))
				htr = HTTPRequest.FromRawTCPMessage(currentMessage)
				self.HandleRequest(htr)
			except Exception as e:
				self.LogError('Error parsing message from client as an HTTP request - {0} - {1}'.format(str(type(e)), str(e.args)))
		else:
			self.LogDebug('No message received from client')
	
		self.LogInfo('Worker shutting down')
		
		try:
			self.ClientSocket.Socket.shutdown(socket.SHUT_RDWR)
			self.ClientSocket.Socket.close()
			self.LogInfo('Closed client socket')
		except Exception as e:
			self.LogError('Error closing client socket - {0} - {1}'.format(str(type(e)), str(e.args)))
		self.State = DeceitfulHTTPServerWorker.WORKERSTATE_STOPPED

	def Stop(self):
		self.State = DeceitfulHTTPServerWorker.WORKERSTATE_STOPPING
		
	def HandleRequest(self, httpRequest):
		try:
			self.ClientSocket.Socket.send('NOT IMPLEMENTED')
		except:
			pass
		
class DeceitfulHTTPServer:
	SERVERSTATE_STOPPED = 0
	SERVERSTATE_RUNNING = 1
	SERVERSTATE_STARTING = 2
	SERVERSTATE_STOPPING = 4
	SERVERSTATE_FORCESTOP = 8
	SERVERSTATE_ERROR = 16
	
	def __init__(self, multiLogger):
		self.DefaultServerName = 'localhost'
		self.MultiLogger = multiLogger
		
		self.UseFQDNsWhereAvailable = True
		self.LookupClientNames = True
		
		self.SSLCertFile = None
		self.SSLKeyFile = None
		self.SSLProtocol = ssl.PROTOCOL_SSLv23
		#self.SSLProtocol = ssl.PROTOCOL_TLSv1
		
		self.SocketTimeout = 20
		#self.BufferSize = 4096
		self.BufferSize = 16384
		#self.BufferSize = 5242880
		self.SocketSpawnDelay = 0.1
		self.ShutdownCheckLimit = 3
		self.ShutdownCheckWait = 1
		self.ListeningLayer3Addresses = []
		self.ServerSockets = []
		self.RequestHandlers = []
		self.Workers = []
		self.CachedLayer3AddressList = libdeceitfulnetwork.CachedLayer3AddressList()
		self.ServerState = DeceitfulHTTPServer.SERVERSTATE_STOPPED

	def GetWorker(self, serverSocket, clientSocket, serverAddressForClient):
		result = DeceitfulHTTPServerWorker(self, serverSocket, clientSocket, serverAddressForClient)
		return result
		
	def GetLogLinePrefix(self, serverSocket):
		result = ''
		if ((serverSocket) and (serverSocket.Layer3Address)):
			result = serverSocket.Layer3Address.GetFormattedName(self.UseFQDNsWhereAvailable) + ' '
		return result
					
	def LogDebug(self, serverSocket, message):
		self.MultiLogger.debug(self.GetLogLinePrefix(serverSocket) + ' - ' + message)

	def LogInfo(self, serverSocket, message):
		self.MultiLogger.info(self.GetLogLinePrefix(serverSocket) + ' - ' + message)

	def LogWarning(self, serverSocket, message):
		self.MultiLogger.warning(self.GetLogLinePrefix(serverSocket) + ' - ' + message)

	def LogError(self, serverSocket, message):
		self.MultiLogger.error(self.GetLogLinePrefix(serverSocket) + ' - ' + message)
		
	def LogCritical(self, serverSocket, message):
		self.MultiLogger.critical(self.GetLogLinePrefix(serverSocket) + ' - ' + message)

	def WaitForConnection(self, serverSocket):
		#useSSL = False
		#if ((self.SSLCertFile) and (self.SSLKeyFile)):
			#useSSL = True
		while 1:
			self.LogInfo(serverSocket, 'Listening for client connections')
			clientSocket = libdeceitfulnetwork.Socket()
			#clientSocketBase = libdeceitfulnetwork.Socket()
			serverAddressForClient = libdeceitfulnetwork.Layer3Address()
			clientNetAddress = []
			gotConnection = False
			try:
				#clientSocketBase.Socket, clientNetAddress = serverSocket.Socket.accept()
				clientSocket.Socket, clientNetAddress = serverSocket.Socket.accept()
				self.LogInfo(serverSocket, 'Connection initiated')
				gotConnection = True
			except Exception as e:
				if ((self.ServerState == DeceitfulHTTPServer.SERVERSTATE_RUNNING) or (self.ServerState == DeceitfulHTTPServer.SERVERSTATE_STARTING)):
					self.LogError(serverSocket, 'Error accepting connection on server socket {0} - {1}'.format(str(type(e)), str(e.args)))
					try:
						clientSocket.Socket.shutdown(socket.SHUT_RDWR)
						clientSocket.Socket.close()
					except Exception as e2:
						pass
				else:
					self.LogDebug(serverSocket, 'An exception occurred while accepting a connection on server socket {0} - {1} - but the server is shutting down, so this is expected'.format(str(type(e)), str(e.args)))
				gotConnection = False
			if (gotConnection):				
				#if (useSSL):
					#self.LogInfo(serverSocket, 'Wrapping connection in SSL/TLS')
					#try:
						#clientSocketBase.Socket.settimeout(self.SocketTimeout)
						#clientSocketBase.Socket.setblocking(0)
						#clientSocket.Socket = ssl.wrap_socket(clientSocketBase.Socket,
							#server_side = True,
							##do_handshake_on_connect=True,
							#suppress_ragged_eofs=True,
							#certfile = self.SSLCertFile,
							#keyfile = self.SSLKeyFile,
							#ssl_version=self.SSLProtocol)
					#except Exception as e:
						#self.LogError(serverSocket, 'Failed to wrap the connection in SSL/TLS - {0} - {1}'.format(str(type(e)), str(e.args)))
						#gotConnection = False
				#else:
					#clientSocket.Socket = clientSocketBase.Socket
				#if (gotConnection):
				clientSocket.Socket.settimeout(self.SocketTimeout)
				clientSocket.Socket.setblocking(0)
				clientIP = clientNetAddress[0]
				clientPort = clientNetAddress[1]
				clientSocket.Layer3Address.IPAddress = clientIP
				clientSocket.Layer3Address.Port = clientPort
				serverNetAddress = clientSocket.Socket.getsockname()
				serverIPForClient = serverNetAddress[0]
				serverPortForClient = serverNetAddress[1]
				serverAddressForClient.IPAddress = serverIPForClient
				serverAddressForClient.Port = serverPortForClient
				if (self.LookupClientNames):
					#clientSocket.Layer3Address.SetNamesUsingLookup(self.MultiLogger)
					clientSocket.Layer3Address = self.CachedLayer3AddressList.GetEntryByAddress(clientIP, self.MultiLogger)
					clientSocket.Layer3Address.Port = clientPort
					serverAddressForClient = self.CachedLayer3AddressList.GetEntryByAddress(serverIPForClient, self.MultiLogger)
					serverAddressForClient.Port = serverPortForClient
				self.LogInfo(serverSocket, 'Received connection from {0}'.format(clientSocket.Layer3Address.GetFormattedName(self.UseFQDNsWhereAvailable)))
				#self.LogDebug(serverSocket, 'getsockname() = "{0}"'.format(clientSocket.Socket.getsockname()))
				
				workerThread = self.GetWorker(serverSocket, clientSocket, serverAddressForClient)
				self.Workers.append(workerThread)
				thread.start_new_thread(workerThread.Run, (None,))
			time.sleep(self.SocketSpawnDelay)
			# worker thread list cleanup
			newThreadList = []
			workerNum = 1
			for wt in self.Workers:
				self.LogDebug(serverSocket, 'Worker {0} - state is {1}'.format(workerNum, wt.State))
				if wt.State == DeceitfulHTTPServerWorker.WORKERSTATE_RUNNING:
					newThreadList.append(wt)
				workerNum = workerNum + 1
			self.LogDebug(serverSocket, 'Current worker list contains {0} workers, pruned list will contain {1} workers'.format(len(self.Workers), len(newThreadList)))
			self.Workers = newThreadList
			if ((self.ServerState != DeceitfulHTTPServer.SERVERSTATE_RUNNING) and (self.ServerState != DeceitfulHTTPServer.SERVERSTATE_STARTING)):
				self.LogInfo(serverSocket, 'Server is shutting down gracefully - ending listening loop')
				break

		try:
			serverSocket.Socket.shutdown(socket.SHUT_RDWR)
			serverSocket.Socket.close()
			self.LogInfo(serverSocket, 'Closed server socket')
		except Exception as e:
			self.LogError(serverSocket, 'Error closing server socket {0} - {1}'.format(str(type(e)), str(e.args)))
				
		self.ServerState = DeceitfulHTTPServer.SERVERSTATE_STOPPED
		
	def Run(self):
		self.ServerState = DeceitfulHTTPServer.SERVERSTATE_STARTING
		listeningPorts = 0
		useSSL = False
		if ((self.SSLCertFile) and (self.SSLKeyFile)):
			useSSL = True
		for listenAddress in self.ListeningLayer3Addresses:
			try:
				#newServerSocket = libdeceitfulnetwork.Socket()
				##newServerSocket.Layer3Address.IPAddress = listenAddress.IPAddress
				##newServerSocket.Layer3Address.Port = listenAddress.Port
				#newServerSocket.Layer3Address = self.CachedLayer3AddressList.GetEntryByAddress(listenAddress.IPAddress, self.MultiLogger)
				#newServerSocket.Layer3Address.Port = listenAddress.Port
				#if ((newServerSocket.Layer3Address.HostName == None) or (newServerSocket.Layer3Address.HostName == '')):
					#newServerSocket.Layer3Address.HostName = self.DefaultServerName
				#if ((newServerSocket.Layer3Address.HostFQDN == None) or (newServerSocket.Layer3Address.HostFQDN == '')):
					#newServerSocket.Layer3Address.HostFQDN = newServerSocket.Layer3Address.HostName
				##newServerSocket.Layer3Address.SetNamesUsingLookup(self.MultiLogger)
				#newServerSocket.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				##newServerSocket.Socket.settimeout(self.SocketTimeout)
				#newServerSocket.Socket.bind((newServerSocket.Layer3Address.IPAddress, newServerSocket.Layer3Address.Port))
				newServerSocket = libdeceitfulnetwork.Socket()
				newServerSocketBase = libdeceitfulnetwork.Socket()
				#newServerSocket.Layer3Address.IPAddress = listenAddress.IPAddress
				#newServerSocket.Layer3Address.Port = listenAddress.Port
				newServerSocketBase.Layer3Address = self.CachedLayer3AddressList.GetEntryByAddress(listenAddress.IPAddress, self.MultiLogger)
				newServerSocketBase.Layer3Address.Port = listenAddress.Port
				if ((newServerSocketBase.Layer3Address.HostName == None) or (newServerSocketBase.Layer3Address.HostName == '')):
					newServerSocketBase.Layer3Address.HostName = self.DefaultServerName
				if ((newServerSocketBase.Layer3Address.HostFQDN == None) or (newServerSocketBase.Layer3Address.HostFQDN == '')):
					newServerSocketBase.Layer3Address.HostFQDN = newServerSocketBase.Layer3Address.HostName
				#newServerSocket.Layer3Address.SetNamesUsingLookup(self.MultiLogger)
				newServerSocketBase.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				#newServerSocket.Socket.settimeout(self.SocketTimeout)
				#newServerSocketBase.Socket.bind((newServerSocket.Layer3Address.IPAddress, newServerSocket.Layer3Address.Port))
				
				if (useSSL):
					self.MultiLogger.info('Wrapping server socket in SSL/TLS')
					try:
						newServerSocket.Socket = ssl.wrap_socket(newServerSocketBase.Socket,
							server_side = True,
							do_handshake_on_connect=True,
							suppress_ragged_eofs=True,
							certfile = self.SSLCertFile,
							keyfile = self.SSLKeyFile,
							ssl_version = self.SSLProtocol)
					except Exception as e:
						self.MultiLogger.error('Failed to wrap the server socket in SSL/TLS - {0} - {1}'.format(str(type(e)), str(e.args)))
						gotConnection = False
				else:
					newServerSocket.Socket = newServerSocketBase.Socket

				newServerSocket.Layer3Address = newServerSocketBase.Layer3Address
				newServerSocketBase.Socket.bind((newServerSocket.Layer3Address.IPAddress, newServerSocket.Layer3Address.Port))
				newServerSocket.Socket.listen(5)
				self.ServerSockets.append(newServerSocket)
				self.MultiLogger.info('Created listener for {0}:{1}'.format(newServerSocket.Layer3Address.IPAddress, newServerSocket.Layer3Address.Port))
				listeningPorts = listeningPorts + 1
			except Exception as e:
				self.MultiLogger.error('Error creating listener on {0}:{1} - {2} - {3}'.format(listenAddress.IPAddress, listenAddress.Port, str(type(e)), str(e.args)))
		if (listeningPorts > 0):
			self.MultiLogger.info('{0} listeners created'.format(listeningPorts))
			for s in self.ServerSockets:
				#thread.start_new_thread(self.WaitForConnection, (s, ))
				try:
					thread.start_new_thread(self.WaitForConnection, (s, ))
					self.MultiLogger.debug('WaitForConnection() thread spawned')
				except Exception as e:
					self.MultiLogger.error('Error starting listener on {0}:{1} - {2} - {3}'.format(s.Layer3Address.IPAddress, s.Layer3Address.Port, str(type(e)), str(e.args)))
			self.ServerState = DeceitfulHTTPServer.SERVERSTATE_RUNNING
		else:
			self.MultiLogger.error('No listeners were successfully created - no connections can be accepted - no work to do')
		
		loopIterations = 0
		loopIterationsReport = 10000
		while (self.ServerState == DeceitfulHTTPServer.SERVERSTATE_RUNNING):
			loopIterations = loopIterations + 1
			if ((loopIterations % loopIterationsReport) == 0):
				self.MultiLogger.debug('Still listening after {0} iterations'.format(loopIterations))
			time.sleep(1)

			# updated cached entries if the threaded lookup is done
			for s in self.ServerSockets:
				currentL3Address = copy.deepcopy(s.Layer3Address)
				newL3Address = self.CachedLayer3AddressList.GetEntryByAddress(currentL3Address.IPAddress, self.MultiLogger)
				if not (currentL3Address.ValuesMatch(newL3Address, multiLogger = self.MultiLogger)):
					self.MultiLogger.debug('Using updated host information from threaded lookup')
					s.Layer3Address = newL3Address
				else:
					msg = 'No new host information obtained from threaded lookup'
					#self.MultiLogger.debug(msg)


	def Stop(self):
		self.ServerState = DeceitfulHTTPServer.SERVERSTATE_STOPPING
		
	def WaitForShutdown(self):
		checkNum = 0
		while (self.ServerState != DeceitfulHTTPServer.SERVERSTATE_STOPPED):
			if (checkNum > self.ShutdownCheckLimit):
				self.MultiLogger.warning('Attempting to forcibly close any remaining open sockets - server ports may still be in use until the OS-level networking subsystem times them out')
				break
			else:
				if (checkNum > 0):
					self.MultiLogger.info('Waiting for running threads to shut down (check {0} of {1})'.format(checkNum, self.ShutdownCheckLimit))
			time.sleep(self.ShutdownCheckWait)
			checkNum = checkNum + 1
		for s in self.ServerSockets:
			#thread.start_new_thread(self.WaitForConnection, (s, ))
			try:
				s.Socket.shutdown(socket.SHUT_RDWR)
				s.Socket.close()
				self.MultiLogger.info('Closed server socket {0}:{1}'.format(s.Layer3Address.IPAddress, s.Layer3Address.Port))
			except Exception as e:
				self.MultiLogger.error('Error closing server socket {0}:{1} - {2} - {3}'.format(s.Layer3Address.IPAddress, s.Layer3Address.Port, str(type(e)), str(e.args)))

	@staticmethod
	def SanitizeURLsLikeApacheHTTPD2(url):
		result = url.replace("<", "&lt;")
		result = result.replace(">", "&gt;")
		return result
				
class DeceitfulHTTPProxy:
	def __init__(self, multiLogger):
		self.MultiLogger = multiLogger
		# rules for handling requests by destination server
		# e.g. when operating as a silent proxy where SSL private keys are available for some (but not all) destination servers
		# these handlers will determine which traffic is subject to SSL inspection or passed unmodified
		self.ServerLevelResponseHandlers = []
		# meta-logic applied before header handlers are given the headers (which may be modified by this logic)
		self.StripUnrecognizedRequestHeaders = False
		self.StripUnrecognizedResponseHeaders = False
		self.StripClientRedirects = False
		self.PreventCaching = False
		

		
		# HTTP version modification (always send same version, etc.)
		# User-Agent modification (stripping distinctive data, etc.)
		# Accept header modification (stripping distinctive data, etc.)
		# Accept-Language header modification (stripping distinctive data, etc.)
		# Cookie modification
		# 