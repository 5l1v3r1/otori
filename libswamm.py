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

import libdeceitfulhttp
import libdeceitfulnetwork
import libfileio
import liblogging
import liboutput
import libswammserverprofiles

__author__ = 'Ben Lincoln - http://www.beneaththewaves.net/'

class SWAMMException(Exception):
    def __init__(self, msg):
        self.msg = msg

class StoredMessage:
	def __init__(self, rawMessage):
		self.RawMessage = rawMessage
		self.TimeStampUTC = datetime.datetime.utcnow()
		
	def GetMessage(self):
		result = '{0}\n\n'.format(liboutput.OutputUtils.GetFormattedDateTime(self.TimeStampUTC))
		result = result + self.RawMessage
		return result
        
class SWAMMWorker(libdeceitfulhttp.DeceitfulHTTPServerWorker):
	def __init__(self, parentServer, serverSocket, clientSocket, serverAddressForClient):
		libdeceitfulhttp.DeceitfulHTTPServerWorker.__init__(self, parentServer, serverSocket, clientSocket, serverAddressForClient)

	def URLBeginsWithPrefix(self, url, prefix):
		self.LogDebug('Checking whether URL "{0}" begins with prefix "{1}"'.format(url, prefix))
		if (len(url) >= len(prefix)):
			urlLeft = liboutput.OutputUtils.Left(url, len(prefix))
			self.LogDebug('Checking whether the leftmost part of the URL ("{0}") matches the prefix "{1}"'.format(urlLeft, prefix))
			if (urlLeft == prefix):
				self.LogDebug('Match found')
				return True
			else:
				self.LogDebug('No match found')
				return False
		else:
			self.LogDebug('URL "{0}" is too short to begin with prefix "{1}"'.format(url, prefix))
		return False
		
	def GetSWAMMKey(self, url, prefix):
		if (len(url) >= len(prefix)):
			result = liboutput.OutputUtils.RightLess(url, len(prefix))
			# get the next URL component, delimited by either path separator or the end of the stem
			rSplit = result.split('?')
			result = rSplit[0]
			rSplit = result.split('/')
			result = rSplit[0]
			self.LogDebug('Extracted key "{0}" from URL "{1}"'.format(result, url))
			return result
		else:
			self.LogError('An attempt was made to extract a SWAMM key from the URL "{0}", but that URL is not long enough to begin with the prefix "{1}"'.format(url, prefix))
			return None

	def StoreMessage(self, responseOriginal, key, rawRequest, append = True):
		response = copy.deepcopy(responseOriginal)
		newMessage = StoredMessage(rawRequest)
		if (key in self.ParentServer.StoredMessages.keys()):
			if (append):
				self.LogDebug('Appending stored message to existing list with key "{0}"'.format(key))
			else:
				self.LogDebug('Overwriting existing stored message with key "{0}"'.format(key))
				self.ParentServer.StoredMessages[key] = []
		else:
			self.LogDebug('Storing message to a new list with key "{0}"'.format(key))
			self.ParentServer.StoredMessages[key] = []

		try:
			self.ParentServer.StoredMessages[key].append(newMessage)
			self.LogDebug('Stored message "{0}"'.format(rawRequest))
			response.ResponseCode = 200
			response.Body = ''
		except Exception as e:
			self.LogError('An exception occurred storing message "{0}" to the list with key "{1}" - {2} - {3}'.format(str(key), str(rawRequest), str(type(e)), str(e.args)))

		return response
		
	def RetrieveMessages(self, responseOriginal, key):
		response = copy.deepcopy(responseOriginal)
		if (key in self.ParentServer.StoredMessages.keys()):
			responseBody = ''
			try:
				storedMessages = self.ParentServer.StoredMessages[key]
				messageNum = 1
				for message in storedMessages:
					responseBody = responseBody + 'Begin message {0}\n'.format(messageNum)
					responseBody = responseBody + message.GetMessage()
					responseBody = responseBody + 'End message {0}\n'.format(messageNum)
					messageNum = messageNum + 1
				response.ResponseCode = 200
				self.LogDebug('Retrieved the following messages from the list with key "{0}"\n{1}'.format(key, responseBody))
			except Exception as e:
				self.LogError('An exception occurred while retrieving existing messages from the list with key "{0}" - {1} - {2}'.format(str(key), str(type(e)), str(e.args)))
				response.ReponseCode = 500
			response.Body = responseBody
		else:
			response.ResponseCode = 404
			self.LogWarning('A request was made to retrieve the message(s) previously stored with with key "{0}", but that key was not found'.format(key))
		return response

	def DeleteMessages(self, responseOriginal, key):
		response = copy.deepcopy(responseOriginal)
		if (key in self.ParentServer.StoredMessages.keys()):
			try:
				self.ParentServer.StoredMessages[key] = None
				del self.ParentServer.StoredMessages[key]
				self.LogDebug('Deleted the message(s) previously stored with with key "{0}"'.format(key))
				response.ResponseCode = 200
			except Exception as e:
				self.LogError('An exception occurred while deleting existing messages from the list with key "{0}" - {1} - {2}'.format(str(key), str(type(e)), str(e.args)))
				response.ReponseCode = 500
		else:
			response.ResponseCode = 404
			self.LogWarning('A request was made to delete the message(s) previously stored with with key "{0}", but that key was not found'.format(key))
		return response

	def StoreRequestResponsePair(self, responseOriginal, key, rawRequest):
		response = copy.deepcopy(responseOriginal)
		newPair = StoredRequestResponsePair()
		gotPair = False
		try:
			newPair = StoredRequestResponsePair.FromSWAMMStoredMessage(rawRequest)
			gotPair = True
		except Exception as e:
			self.LogError('Could not convert the raw request "{0}" to a request/response pair - {1} - {2}'.format(str(rawRequest), str(type(e)), str(e.args)))
			gotPair = False
		if (gotPair):
			if (key in self.ParentServer.StoredRequestResponsePairs.keys()):
				self.LogDebug('Overwriting existing stored request/response pair with key "{0}"'.format(key))
			else:
				self.LogDebug('Adding new stored request/response pair with key "{0}"'.format(key))
			try:
				self.ParentServer.StoredRequestResponsePairs[key] = newPair
				self.LogDebug('Stored request/response pair "{0}"'.format(rawRequest))
				response.ResponseCode = 200
				response.Body = ''
			except Exception as e:
				self.LogError('An exception occurred storing message "{0}" to the list with key "{1}" - {2} - {3}'.format(str(key), str(rawRequest), str(type(e)), str(e.args)))
		return response
		
	def DeleteRequestResponsePair(self, responseOriginal, key):
		response = copy.deepcopy(responseOriginal)
		if (key in self.ParentServer.StoredRequestResponsePairs.keys()):
			try:
				self.ParentServer.StoredRequestResponsePairs[key] = None
				del self.ParentServer.StoredRequestResponsePairs[key]
				self.LogDebug('Deleted the stored request/response pair previously stored with with key "{0}"'.format(key))
				response.ResponseCode = 200
			except Exception as e:
				self.LogError('An exception occurred while deleting the stored request/response pair from the list with key "{0}" - {1} - {2}'.format(str(key), str(type(e)), str(e.args)))
				response.ReponseCode = 500
			self.LogDebug('Overwriting existing stored request/response pair with key "{0}"'.format(key))
		else:
			self.LogWarning('A request was made to delete the stored request/response pair previously stored with with key "{0}", but that key was not found'.format(key))
		return response
		
	def HandleRequest(self, httpRequest):
		self.LogDebug('Generating response')
		response = libdeceitfulhttp.HTTPResponse()
		#response.ResponseCode = 404
		response.ResponseCode = self.ParentServer.ServerProfile.DefaultResponseCode
		#defaultResponseCode = 404
		#response = self.ParentServer.ServerProfile.GetResponse(httpRequest, self.ClientSocket.Layer3Address, self.ServerSocket.Layer3Address, defaultResponseCode, multiLogger = self.ParentServer.MultiLogger)
		#response.ResponseReason = libdeceitfulhttp.HTTPResponse.GetHTTPResponseReasonFromCode(response.ResponseCode)
		#sUrl = libdeceitfulhttp.DeceitfulHTTPServer.SanitizeURLsLikeApacheHTTPD2(httpRequest.URL)
		#response.Body = '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n<html><head>\n<title>404 Not Found</title>\n</head><body>\n<h1>Not Found</h1>\n<p>The requested URL {0} was not found on this server.</p>\n<hr>\n<address>Apache/2.2.22 Server at {1} Port {2}</address>\n</body></html>'.format(sUrl, self.ServerSocket.Layer3Address.IPAddress, self.ServerSocket.Layer3Address.Port)
		#response.Headers['Server'] = 'Apache'
		
		specialURL = False
		#if (self.ParentServer is SWAMMServer):
		#self.LogDebug('Parent server is a SWAMM server instance')
		swammKey = ''
		foundRequestType = False
		if not (foundRequestType):
			if self.URLBeginsWithPrefix(httpRequest.URL, self.ParentServer.ReadPrefix):
				swammKey = self.GetSWAMMKey(httpRequest.URL, self.ParentServer.ReadPrefix)
				self.LogDebug('This is a SWAMM read URL with key "{0}"'.format(swammKey))
				response = self.RetrieveMessages(response, swammKey)
				foundRequestType = True
				specialURL = True
		if not (foundRequestType):
			if self.URLBeginsWithPrefix(httpRequest.URL, self.ParentServer.WritePrefix):
				swammKey = self.GetSWAMMKey(httpRequest.URL, self.ParentServer.WritePrefix)
				self.LogDebug('This is a SWAMM write URL with key "{0}"'.format(swammKey))
				response = self.StoreMessage(response, swammKey, httpRequest.RawRequest, False)
				foundRequestType = True
				specialURL = True
		if not (foundRequestType):
			if self.URLBeginsWithPrefix(httpRequest.URL, self.ParentServer.AppendPrefix):
				swammKey = self.GetSWAMMKey(httpRequest.URL, self.ParentServer.AppendPrefix)
				self.LogDebug('This is a SWAMM append URL with key "{0}"'.format(swammKey))
				response = self.StoreMessage(response, swammKey, httpRequest.RawRequest, True)
				foundRequestType = True
				specialURL = True
		if not (foundRequestType):
			if self.URLBeginsWithPrefix(httpRequest.URL, self.ParentServer.DeletePrefix):
				swammKey = self.GetSWAMMKey(httpRequest.URL, self.ParentServer.DeletePrefix)
				self.LogDebug('This is a SWAMM delete URL with key "{0}"'.format(swammKey))
				response = self.DeleteMessages(response, swammKey)
				foundRequestType = True
				specialURL = True
		if not (foundRequestType):
			if self.URLBeginsWithPrefix(httpRequest.URL, self.ParentServer.StoredPairAddPrefix):
				swammKey = self.GetSWAMMKey(httpRequest.URL, self.ParentServer.StoredPairAddPrefix)
				self.LogDebug('This is a SWAMM stored request/response pair store URL with key "{0}"'.format(swammKey))
				response = self.StoreRequestResponsePair(response, swammKey, httpRequest.RawRequest)
				foundRequestType = True
				specialURL = True
		if not (foundRequestType):
			if self.URLBeginsWithPrefix(httpRequest.URL, self.ParentServer.StoredPairDeletePrefix):
				swammKey = self.GetSWAMMKey(httpRequest.URL, self.ParentServer.StoredPairDeletePrefix)
				self.LogDebug('This is a SWAMM stored request/response pair delete URL with key "{0}"'.format(swammKey))
				response = self.DeleteRequestResponsePair(response, swammKey)
				foundRequestType = True
				specialURL = True
		if not (foundRequestType):
			if ((self.ParentServer.StoredRequestResponsePairs) and (len(self.ParentServer.StoredRequestResponsePairs) > 0)):
				for srrpKey in self.ParentServer.StoredRequestResponsePairs.keys():
					self.LogDebug('Checking stored request/response pair with key "{0}"'.format(srrpKey))
					srrp = self.ParentServer.StoredRequestResponsePairs[srrpKey]
					srrp.MultiLogger = self.ParentServer.MultiLogger
					if (srrp.MatchesRequest(httpRequest)):
						self.LogDebug('Stored request/response pair with key "{0}" matches this request - will use the stored response'.format(srrpKey))
						response = srrp.Response
						foundRequestType = True
						specialURL = True
						break
					else:
						self.LogDebug('Stored request/response pair with key "{0}" does not match this request'.format(srrpKey))
		if (specialURL):
			dummy = 1
		else:
			self.LogDebug('This is a regular URL')
		try:
			if (self.ParentServer.RestrictHTTPMethods):
				if (httpRequest.HTTPMethod in self.ParentServer.AllowedHTTPMethods):
					self.LogDebug('The request method "{0}" is allowed by the current configuration'.format(httpRequest.HTTPMethod))
				else:
					self.LogDebug('The request method "{0}" is not allowed by the current configuration, and a Method Not Allowed response will be returned'.format(httpRequest.HTTPMethod))
					response = self.ParentServer.ServerProfile.GetMethodNotAllowedResponseResponse(httpRequest, self.ClientSocket.Layer3Address, self.ServerAddressForClient, self.ParentServer.MultiLogger)
			else:
				self.LogDebug('The request method "{0}" is allowed by the current configuration, because request method restrictions are disabled'.format(httpRequest.HTTPMethod))
			if (httpRequest.HTTPMethod == 'OPTIONS'):
				self.LogDebug('This is an OPTIONS request, so the appropriate response will be obtained from the server profile')
				#response = self.ParentServer.ServerProfile.GetOptionsResponse(httpRequest, self.ClientSocket.Layer3Address, self.ServerSocket.Layer3Address, response.ResponseCode, self.ParentServer.MultiLogger)
				response = self.ParentServer.ServerProfile.GetOptionsResponse(httpRequest, self.ClientSocket.Layer3Address, self.ServerAddressForClient, response.ResponseCode, self.ParentServer.MultiLogger)
			#revisedResponseTemplate = self.ParentServer.ServerProfile.GetResponse(httpRequest, self.ClientSocket.Layer3Address, self.ServerSocket.Layer3Address, response.ResponseCode, self.ParentServer.MultiLogger)
			revisedResponseTemplate = self.ParentServer.ServerProfile.GetResponse(httpRequest, self.ClientSocket.Layer3Address, self.ServerAddressForClient, response.ResponseCode, self.ParentServer.MultiLogger)
			self.LogDebug('Response template obtained')
			
			response.MultiLogger = self.ParentServer.MultiLogger
			#if ((response.ResponseReason == None) or (response.ResponseReason == '')):
			#	response.ResponseReason = libdeceitfulhttp.HTTPResponse.GetHTTPResponseReasonFromCode(response.ResponseCode)
			if ((response.ResponseReason == None) or (response.ResponseReason == '')):
				response.ResponseReason = revisedResponseTemplate.ResponseReason
				self.LogDebug('No response reason was set, so the reason of "{0}" from the response template was used'.format(revisedResponseTemplate.ResponseReason))
			if ((response.ResponseCode != 200)):
				response.Body = revisedResponseTemplate.Body
				self.LogDebug('The HTTP response code was {0} instead of 200, so the body from the response template was used'.format(revisedResponseTemplate.ResponseCode))
			existingHeaders = response.GetHeaders()
			existingHeaderNames = []
			for eh in existingHeaders:
				if (len(eh) < 2):
					self.LogDebug('Malformed existing header returned by GetHeaders()')
				else:
					ehName = eh[0]
					ehValue = eh[1]
				self.LogDebug('Adding existing header "{0}" with value "{1}" to list'.format(ehName, ehValue))
				existingHeaderNames.append(ehName)
			for th in revisedResponseTemplate.GetHeaders():
				if (len(th) < 2):
					self.LogDebug('Malformed template header returned by GetHeaders()')
				else:
					thName = th[0]
					thValue = th[1]
					#self.LogDebug('Adding or replacing header "{0}" with value "{1}" (from response template)'.format(thName, thValue))
					#response.AddOrReplaceHeader(thName, thValue)
					if (thName in existingHeaderNames):
						self.LogDebug('Skipping template header "{0}" with value "{1}" because the response already contains a header of this type'.format(thName, thValue))
					else:
						self.LogDebug('Adding header "{0}" with value "{1}" (from response template)'.format(thName, thValue))
						response.AddOrReplaceHeader(thName, thValue)

			response.AddOrReplaceHeader('Content-Length', len(response.Body))
			self.LogDebug('Set Content-Length header to {0}'.format(len(response.Body)))

			# handle HEAD requests properly
			if (httpRequest.HTTPMethod == 'HEAD'):
				response.Body = None
				self.LogDebug('The HTTP request method was HEAD, so the body will not be returned')
			
			self.LogDebug('Response HTTP version "{0}"'.format(str(response.HTTPVersion)))
			self.LogDebug('Response HTTP response code {0}'.format(str(response.ResponseCode)))
			self.LogDebug('Response HTTP response reason "{0}"'.format(str(response.ResponseCode)))
			self.LogDebug('Response HTTP response headers "{0}"'.format(str(response.Headers)))
			self.LogDebug('Response HTTP response body:\n{0}'.format(str(response.Body)))
			responseData = response.ToRawTCPMessage()
			self.LogDebug('Sending response:\n{0}'.format(responseData))
			self.ClientSocket.Socket.send(responseData)
		except Exception as e:
			self.LogError('Error sending response to client - {0} - {1}'.format(str(type(e)), str(e.args)))
			pass

# used for storing more-or-less exact client requests and the responses that should be sent if they are received
class StoredRequestResponsePair:
	def __init__(self):
		self.Request = libdeceitfulhttp.HTTPRequest()
		self.Response = libdeceitfulhttp.HTTPResponse()
		self.RequestURLRegex = None
		self.MatchRequestMethod = True
		self.MatchRequestURLParameters = False
		self.MatchRequestHeaders = False
		self.MatchRequestBody = False
		self.MultiLogger = None

	def MatchesRequest(self, httpRequest):
		# check method
		msg = ''
		if (self.MultiLogger):
			self.MultiLogger.debug('Comparing self HTTP method "{0}" to HTTP request method "{1}"'.format(self.Request.HTTPMethod, httpRequest.HTTPMethod))
		if (self.MatchRequestMethod):
			if (self.Request.HTTPMethod == httpRequest.HTTPMethod):
				msg = 'Request method matches'
			else:
				msg = 'Request method does not match - failing this comparison'
				return False
				
		if (self.MultiLogger):
			self.MultiLogger.debug(msg)
			
		# check URL
		msg = ''
		if ((self.RequestURLRegex) and (self.RequestURLRegex is not None)):
			if (self.MultiLogger):
				self.MultiLogger.debug('Comparing self URL regex "{0}" to HTTP request URL "{1}"'.format(self.RequestURLRegex, httpRequest.URL))
			rxURL = re.compile(self.RequestURLRegex)
			m = rxURL.match(httpRequest.URL)
			if (m):
				dummy = 1
				msg = 'Request URL matches regex'
			else:
				msg = 'Request URL does not match regex - failing this comparison'
				return False
		else:
			if (self.MultiLogger):
				self.MultiLogger.debug('Comparing self URL "{0}" to HTTP request URL "{1}"'.format(self.Request.URL, httpRequest.URL))
			urlIsMatch = False
			if (self.Request.URL == httpRequest.URL):
				dummy = 1
				urlIsMatch = True
				msg = 'Request URL matches'
			# hack due to unexplained behaviour
			#if (urlIsMatch == False):
				#rURLLen = len(self.Request.URL)
				#hURLLen = len(httpRequest.URL)
				##if (self.MultiLogger):
				##	self.MultiLogger.debug('rURLLen = {0}, hURLLen = {1}'.format(rURLLen, hURLLen))
				#rURL = self.Request.URL
				#hURL = httpRequest.URL
				#if (hURLLen < rURLLen):
					#rURL = liboutput.OutputUtils.Right(rURL, hURLLen)
				#else:
					#if (rURLLen < hURLLen):
						#hURL = liboutput.OutputUtils.Right(hURL, rURLLen)
				#if (self.MultiLogger):
					#self.MultiLogger.debug('Comparing (truncated) self URL "{0}" to HTTP request URL "{1}"'.format(rURL, hURL))
				#if (rURL == hURL):
					#dummy = 1
					#urlIsMatch = True
					#msg = 'Request URL matches'
			if (urlIsMatch == False):
				msg = 'Request URL does not match - failing this comparison'
				return False

		if (self.MultiLogger):
			self.MultiLogger.debug(msg)
			
		# functionality below this line not yet implemented
		# check URL parameters
		if (self.MatchRequestURLParameters):
			dummy = 1

		# check URL parameters
		if (self.MatchRequestHeaders):
			dummy = 1

		# check URL parameters
		if (self.MatchRequestBody):
			dummy = 1

		return True

	def BoolToInt(self, boolean):
		if (boolean):
			return 1
		else:
			return 0

	def IntToBool(self, intVal):
		if (intVal == 0):
			return False
		else:
			return True
			
	def ToSWAMMStoredMessage(self):
		result = '[[[Begin Options]]]\n'
		result = result + 'RequestURLRegex:{0}\n'.format(self.RequestURLRegex)
		result = result + 'MatchRequestMethod:{0}\n'.format(self.BoolToInt(self.MatchRequestMethod))
		result = result + 'MatchRequestURLParameters:{0}\n'.format(self.BoolToInt(self.MatchRequestURLParameters))
		result = result + 'MatchRequestHeaders:{0}\n'.format(self.BoolToInt(self.MatchRequestHeaders))
		result = result + 'MatchRequestBody:{0}\n'.format(self.BoolToInt(self.MatchRequestBody))
		result = result + '[[[End Options]]]\n'

		result = result + '[[[Begin Request]]]'
		result = result + base64.b64encode(self.Request.ToRawTCPMessage())
		result = result + '[[[End Request]]]\n'

		result = result + '[[[Begin Response]]]'
		result = result + base64.b64encode(self.Response.ToRawTCPMessage())
		result = result + '[[[End Response]]]\n'

		return result

	@staticmethod
	def GetBlock(storedMessage, blockSectionName):
		result = None
		rsBlock = '.*(\[\[\[Begin {0}\]\]\])(?P<blockcontents>.*)(\[\[\[End {1}\]\]\]).*'.format(blockSectionName, blockSectionName)
		rx = re.compile(rsBlock, flags=re.MULTILINE|re.DOTALL)
		m = rx.match(storedMessage)
		if (m):
			result = m.group('blockcontents')
			#print 'Found block:\n{0}'.format(result)
			return result
		else:
			errMsg = 'Error - could not find block'
			#print errMsg
			dummy = 1
		return None

	@staticmethod
	def GetValueIfMatch(line, parameterName):
		pnLen = len(parameterName)
		if (len(line) <= pnLen):
			return None
		if (liboutput.OutputUtils.Left(line, pnLen) == parameterName):
			return liboutput.OutputUtils.RightLess(line, pnLen)
		return None

	@staticmethod
	def FromSWAMMStoredMessage(storedMessage):
		result = StoredRequestResponsePair()
		#rsOptions = r"(\[\[\[Begin Options\]\]\])(?P<options>.*)(\[\[\[End Options\]\]\])"
		#rx = re.compile(rsOptions, flags=re.MULTILINE|re.DOTALL)
		#m = rx.match(result)
		#if (m):
			#print 'Found options block:\n{0}'.format(m.group('options'))
		#else:
			#print 'Error - could not find options block'
			#dummy = 1
		optionsBlock = StoredRequestResponsePair.GetBlock(storedMessage, 'Options')
		if (optionsBlock):
			obLines = optionsBlock.splitlines()
			for l in obLines:
				#print 'Debug - line "{0}"'.format(l)
				v = StoredRequestResponsePair.GetValueIfMatch(l, 'RequestURLRegex:')
				if (v):
					result.RequestURLRegex = v
					if (v == "None"):
						result.RequestURLRegex = None
					#print 'Debug - set result.RequestURLRegex to "{0}"'.format(result.RequestURLRegex)
				v = StoredRequestResponsePair.GetValueIfMatch(l, 'MatchRequestMethod:')
				if (v):
					result.MatchRequestMethod = result.IntToBool(v)
					#print 'Debug - set result.MatchRequestMethod to "{0}"'.format(result.MatchRequestMethod)
				v = StoredRequestResponsePair.GetValueIfMatch(l, 'MatchRequestURLParameters:')
				if (v):
					result.MatchRequestURLParameters = result.IntToBool(v)
					#print 'Debug - set result.MatchRequestURLParameters to "{0}"'.format(result.MatchRequestURLParameters)
				v = StoredRequestResponsePair.GetValueIfMatch(l, 'MatchRequestHeaders:')
				if (v):
					result.MatchRequestHeaders = result.IntToBool(v)
					#print 'Debug - set result.MatchRequestHeaders to "{0}"'.format(result.MatchRequestHeaders)
				v = StoredRequestResponsePair.GetValueIfMatch(l, 'MatchRequestBody:')
				if (v):
					result.MatchRequestBody = result.IntToBool(v)
					#print 'Debug - set result.MatchRequestBody to "{0}"'.format(result.MatchRequestBody)
		else:
			errMsg = 'Debug - error - no options block found'
			#print errMsg
		
		requestBlock = StoredRequestResponsePair.GetBlock(storedMessage, 'Request')
		if (requestBlock):
			try:
				bdecoded = base64.b64decode(requestBlock)
				try:
					result.Request = libdeceitfulhttp.HTTPRequest.FromRawTCPMessage(bdecoded)
				except Exception as e:
					errMsg = 'Error - could not convert the request block into an HTTP request object - {0} - {1}'.format(str(type(e)), str(e.args))
					#print errMsg
			except Exception as e:
				errMsg = 'Error - could not decode the request block'
				#print errMsg
		else:
			errMsg = 'Debug - error - no request block found'
			#print errMsg

		responseBlock = StoredRequestResponsePair.GetBlock(storedMessage, 'Response')
		if (responseBlock):
			try:
				bdecoded = base64.b64decode(responseBlock)
				try:
					result.Response = libdeceitfulhttp.HTTPResponse.FromRawTCPMessage(bdecoded)
				except Exception as e:
					errMsg = 'Error - could not convert the response block into an HTTP response object - {0} - {1}'.format(str(type(e)), str(e.args))
					#print errMsg
			except Exception as e:
				errMsg = 'Error - could not decode the response block'
				#print errMsg
		else:
			errMsg = 'Debug - error - no response block found'
			#print errMsg

		return result

class SWAMMURLSet():
	def __init__(self):
		self.BaseURL = None
		self.ReadURL = None
		self.WriteURL = None
		self.AppendURL = None
		self.DeleteURL = None
		self.StoreAddURL = None
		self.StoreDeleteURL = None
	
class SWAMMServer(libdeceitfulhttp.DeceitfulHTTPServer):
	def __init__(self, multiLogger, masterPrefix = None, readPrefix = None, writePrefix = None, appendPrefix = None, deletePrefix = None, storedPairAddPrefix = None, storedPairDeletePrefix = None):
		libdeceitfulhttp.DeceitfulHTTPServer.__init__(self, multiLogger)
		# Using 62 characters, a prefix length of:
		#	1 = 62 combinations
		#	2 = 3844 combinations
		#	3 = 238328 combinations
		#	4 = 14776336 combinations
		#	5 = 916132832 combinations
		#	6 = 56800235584 combinations
		# 4 should definitely be enough, 3 probably is too
		#self.ServerProfile = libswammserverprofiles.HTTPServerResponseProfileApache2222Generic()
		self.ServerProfile = libswammserverprofiles.HTTPServerResponseProfileApacheCoyote11()
		self.ServerProfile.UseResponseBodyFiles = True
		self.RestrictHTTPMethods = True
		self.AllowedHTTPMethods = []
		self.AllowedHTTPMethods.append('GET')
		self.AllowedHTTPMethods.append('POST')
		self.AllowedHTTPMethods.append('HEAD')
		self.AllowedHTTPMethods.append('OPTIONS')
		self.PrefixGenerator = liboutput.RandomUniqueTextGenerator()
		self.PrefixGenerator.MultiLogger = multiLogger
		prefixMinLength = 3
		prefixMaxLength = 3
		masterPrefixLength = random.randint(prefixMinLength, prefixMaxLength)
		readPrefixLength = random.randint(prefixMinLength, prefixMaxLength)
		writePrefixLength = random.randint(prefixMinLength, prefixMaxLength)
		appendPrefixLength = random.randint(prefixMinLength, prefixMaxLength)
		deletePrefixLength = random.randint(prefixMinLength, prefixMaxLength)
		storedPairAddPrefixLength = random.randint(prefixMinLength, prefixMaxLength)
		storedPairDeletePrefixLength = random.randint(prefixMinLength, prefixMaxLength)
		self.MasterPrefix = None
		self.ReadPrefix = None
		self.WritePrefix = None
		self.AppendPrefix = None
		self.DeletePrefix = None
		self.StoredPairAddPrefix = None
		self.StoredPairDeletePrefix = None
		
		#self.UsedPrefixes = []
		if (masterPrefix):
			self.MasterPrefix = masterPrefix
			#self.UsedPrefixes.append(masterPrefix)
			self.PrefixGenerator.UsedValues.append(masterPrefix)
		else:
			self.MasterPrefix = '/' + self.GetNextUnusedPrefix(readPrefixLength) + '/'
		self.MultiLogger.info('Set master prefix "{0}"'.format(self.MasterPrefix))


		if (readPrefix):
			self.VerifyPrefixIsUnused(readPrefix)
			self.ReadPrefix = readPrefix
			#self.UsedPrefixes.append(readPrefix)
			self.PrefixGenerator.UsedValues.append(readPrefix)
		else:
			self.ReadPrefix = self.MasterPrefix + self.GetNextUnusedPrefix(readPrefixLength) + '/'
		self.MultiLogger.info('Set read prefix "{0}"'.format(self.ReadPrefix))


		if (writePrefix):
			self.VerifyPrefixIsUnused(writePrefix)
			self.WritePrefix = writePrefix
			#self.UsedPrefixes.append(writePrefix)
			self.PrefixGenerator.UsedValues.append(writePrefix)
		else:
			self.WritePrefix = self.MasterPrefix + self.GetNextUnusedPrefix(writePrefixLength) + '/'
		self.MultiLogger.info('Set write prefix "{0}"'.format(self.WritePrefix))

		if (appendPrefix):
			self.VerifyPrefixIsUnused(appendPrefix)
			self.AppendPrefix = appendPrefix
			#self.UsedPrefixes.append(appendPrefix)
			self.PrefixGenerator.UsedValues.append(appendPrefix)
		else:
			self.AppendPrefix = self.MasterPrefix + self.GetNextUnusedPrefix(appendPrefixLength) + '/'
		self.MultiLogger.info('Set append prefix "{0}"'.format(self.AppendPrefix))

		if (deletePrefix):
			self.VerifyPrefixIsUnused(deletePrefix)
			self.DeletePrefix = deletePrefix
			#self.UsedPrefixes.append(deletePrefix)
			self.PrefixGenerator.UsedValues.append(deletePrefix)
		else:
			self.DeletePrefix = self.MasterPrefix + self.GetNextUnusedPrefix(deletePrefixLength) + '/'
		self.MultiLogger.info('Set delete prefix "{0}"'.format(self.DeletePrefix))

		if (storedPairAddPrefix):
			self.VerifyPrefixIsUnused(storedPairAddPrefix)
			self.StoredPairAddPrefix = storedPairAddPrefix
			#self.UsedPrefixes.append(storedPairAddPrefix)
			self.PrefixGenerator.UsedValues.append(storedPairAddPrefix)
		else:
			self.StoredPairAddPrefix = self.MasterPrefix + self.GetNextUnusedPrefix(storedPairAddPrefixLength) + '/'
		self.MultiLogger.info('Set stored pair add prefix "{0}"'.format(self.StoredPairAddPrefix))

		if (storedPairDeletePrefix):
			self.VerifyPrefixIsUnused(storedPairDeletePrefix)
			self.StoredPairDeletePrefix = storedPairDeletePrefix
			#self.UsedPrefixes.append(storedPairDeletePrefix)
			self.PrefixGenerator.UsedValues.append(storedPairDeletePrefix)
		else:
			self.StoredPairDeletePrefix = self.MasterPrefix + self.GetNextUnusedPrefix(storedPairDeletePrefixLength) + '/'
		self.MultiLogger.info('Set stored pair delete prefix "{0}"'.format(self.StoredPairDeletePrefix))
		
		self.StoredMessages = {}
		self.StoredRequestResponsePairs = {}


	def GetNextUnusedPrefix(self, prefixLength):
		#result = liboutput.OutputUtils.GenerateRandomMixedCaseAlphaNumericChars(prefixLength)
		#while (result in self.UsedPrefixes):
			#result = liboutput.OutputUtils.GenerateRandomMixedCaseAlphaNumericChars(prefixLength)
		#self.UsedPrefixes.append(result)
		#return result
		return self.PrefixGenerator.GetNextUnusedText(prefixLength)
		
	def VerifyPrefixIsUnused(self, newPrefix):
		#if (newPrefix in self.UsedPrefixes):
			#errMsg = 'The prefix "{0}" is already in the list of prefixes for this server instance - prefixes must be unique'.format(newPrefix)
			#self.MultiLogger.critical(errMsg)
			#raise SWAMMException(errMsg)
		#return True
		return self.PrefixGenerator.VerifyTextIsUnused(newPrefix)
		
	def GetWorker(self, serverSocket, clientSocket, serverAddressForClient):
		result = SWAMMWorker(self, serverSocket, clientSocket, serverAddressForClient)
		return result
	
	
	
	
	
	
	