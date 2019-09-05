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

import inspect
import os
import random
import re
import sys

# Contains utility classes for file I/O
class Error(Exception):
	pass
	
class FileReadError(Error):
	def __init__(self, msg):
		self.msg = msg
        
class FileWriteError(Error):
	def __init__(self, msg):
		self.msg = msg

class PathNotFoundException(Exception):
	def __init__(self, msg):
		self.msg = msg

class LocalizedPath:
	@staticmethod
	def GetLocalizedPath(basePath, desiredLocale, defaultLocale):
		checkPath = basePath.replace('%LOCALE%', desiredLocale)
		if (os.path.exists(checkPath)):
			return checkPath
		checkPath = basePath.replace('%LOCALE%', defaultLocale)
		if (os.path.exists(checkPath)):
			return checkPath
		if (os.path.exists(basePath)):
			return basePath		
		raise PathNotFoundException('Could not find a real path based on the string "{0}" using the desired locale of "{1}", the default locale of "{2}", or the string itself with no modifications'.format(basePath, desiredLocale, defaultLocale)) 
        
class FileReader:
# Loads a file in as one big string
	@staticmethod
	def getFileAsString(inputFilePath):
		result = ''
		try:
			f = open(inputFilePath, 'rb')
			result = f.read()
			#print result
			f.close()
		except:
			raise FileReadError('Could not open the file (' + inputFilePath + ') - please check that it is present and accessible to the current user.')
		return result
		
# Loads a file in as a list
	@staticmethod
	def getFileAsList(inputFilePath):
		return FileReader.getFileAsString(inputFilePath).splitlines()
		
	@staticmethod
	def getAbsoluteFilePathFromModuleBase(inputFileRelativePath):
		baseDirPath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
		result = baseDirPath + inputFileRelativePath
		return result

class FileWriter:
	@staticmethod
	def WriteFile(outputFilePath, content, mode = 'w'):
		parentPath = os.path.dirname(outputFilePath)
		if not (os.path.exists(parentPath)):
			try:
				os.makedirs(parentPath)
			except:
				raise FileWriteError('Could not create the parent directory (' + parentPath + ') for the file "' + outputFilePath + '"')
		try:
			f = open(outputFilePath, mode)
			f.write(content)
			f.close()
		except:
			raise FileWriteError('Could not open the file (' + outputFilePath + ') - please check that it is present and accessible to the current user.')

# Loads a file in once, then returns random lines from it as necessary
class RandomFileLineGenerator:
	def __init__(self, inputFilePath):
		self.dictionaryEntries = FileReader.getFileAsList(inputFilePath)
		
	def getRandomEntry(self):
		entryNum = random.randint(0, len(self.dictionaryEntries) - 1)
		return self.dictionaryEntries[entryNum].strip()
		
	def getCount(self):
		return len(self.dictionaryEntries)
		

# Returns a random filename from a directory
class RandomFileSelector:
	def __init__(self, baseDirectory):
		self.FileList = []
		if not (os.path.exists(baseDirectory)):
			raise PathNotFoundException('The path "{0}" does not exist or could not be accessed'.format(baseDirectory))
		contents = os.listdir(baseDirectory)
		for entry in contents:
			filePath = os.path.join(baseDirectory, entry)
			if (os.path.isfile(filePath)):
				self.FileList.append(filePath)
				
	def GetRandomEntry(self):
		entryNum = random.randint(0, len(self.FileList) - 1)
		return self.FileList[entryNum]
		
	def GetCount(self):
		return len(self.FileList)
		
		
		