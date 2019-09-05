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

import datetime
import random
import re
import subprocess

import liblogging


class IndexOutOfBoundsException(Exception):
    def __init__(self, msg):
        self.msg = msg
        
class DuplicateUniqueValueException(Exception):
    def __init__(self, msg):
        self.msg = msg

class RandomUniqueTextGenerator:
	def __init__(self):
		self.UsedValues = []
		self.MultiLogger = None
	
	def GetText(self, textLength):
		return OutputUtils.GenerateRandomMixedCaseAlphaNumericChars(textLength)
	
	def GetNextUnusedText(self, textLength):
		result = OutputUtils.GenerateRandomMixedCaseAlphaNumericChars(textLength)
		while (result in self.UsedValues):
			result = OutputUtils.GenerateRandomMixedCaseAlphaNumericChars(textLength)
		self.UsedValues.append(result)
		return result
		
	def VerifyTextIsUnused(self, newText):
		if (newText in self.UsedValues):
			errMsg = 'The value "{0}" is already in a list of values which must be unique'.format(newText)
			if (self.MultiLogger):
				self.MultiLogger.critical(errMsg)
			raise DuplicateUniqueValueException(errMsg)
		return True
		
class RandomUniqueLowercaseAlphaTextGenerator(RandomUniqueTextGenerator):
	def __init__(self):
		RandomUniqueTextGenerator.__init__(self)
		
	def GetText(self, textLength):
		return OutputUtils.GenerateRandomLowercaseAlphaChars(textLength)
        
class OutputUtils:
	@staticmethod
	def GetTerminalWidth():
		return int(subprocess.Popen(['tput', 'cols'], stdout=subprocess.PIPE).stdout.read())
		
	@staticmethod
	def CenterString(terminalWidth, text):
		textFormatted = text
		strippedText = liblogging.ANSITextFormat.StripANSITermCodes(text)
		stringWidth = (len(strippedText))
		if ((stringWidth + 2) < terminalWidth):
			remainder = int((terminalWidth - stringWidth) / 2)
			padding = ''
			for p in range(0, remainder):
				padding = padding + ' '
			textFormatted = padding + textFormatted
		return textFormatted
		
	@staticmethod
	def RepeatString(text, numTimes):
		result = ''
		for i in range (0, numTimes):
			result = result + text
		return result
		
	@staticmethod
	def PadToLength(text, length, padLeft = False):
		result = ' ' + text
		addLength = length - len(liblogging.ANSITextFormat.StripANSITermCodes(text))
		padText = ''
		if (addLength > 0):
			padText = ' '
			while (len(padText) < addLength):
				padText = padText + ' '
		if (padLeft):
			return padText + text
		return text + padText
		
	@staticmethod
	def CenterStringWithPaddingChars(terminalWidth, leftPadChar, text, rightPadChar):
		textFormatted = ''
		strippedText = liblogging.ANSITextFormat.StripANSITermCodes(text)
		stringWidth = (len(strippedText))
		#if ((stringWidth + 2) < terminalWidth):
		if ((stringWidth) < terminalWidth):
			#labelWidth = len(strippedText)
			remainder = int((terminalWidth - stringWidth) / 2)
			textFormatted = textFormatted + OutputUtils.RepeatString(leftPadChar, remainder)
			textFormatted = textFormatted + text
			currentLength = len(liblogging.ANSITextFormat.StripANSITermCodes(textFormatted)) + remainder
			if (currentLength < terminalWidth):
				remainder = remainder + (terminalWidth - currentLength)
			textFormatted = textFormatted + OutputUtils.RepeatString(rightPadChar, remainder)
			# catch off-by-one-character-width conditions
			if (len(textFormatted) < terminalWidth):
				while (len(textFormatted) < terminalWidth):
					textFormatted = textFormatted + rightPadChar
		else:
			# should probably enhance this to break to multiple lines
			textFormatted = text
		return textFormatted
		
	#@staticmethod
	#def BreakTextToLinesByWords(text, lineLength):
		#result = []
		#allWords = text.split(' ')
		#currentLine = ''
		#currentWordNum = 0
		#numWords = len(allWords)
		#while (currentWordNum < numWords):
			#currentWord = allWords[currentWordNum]
			#currentLineLength = len(liblogging.ANSITextFormat.StripANSITermCodes(currentLine))
			#wordLength = len(liblogging.ANSITextFormat.StripANSITermCodes(currentWord))
			#if ((currentLineLength + wordLength) < lineLength):
				#if ('\n' in currentWord):
					#print 'Debug: current line: "' + currentWord + '"'
					#cwLines = currentWord.splitlines()
					#for cwl in cwLines:
						#print 'Debug: current line: "' + cwl + '"'
					#currentLine = currentLine + cwLines[0].strip()
					#result.append(currenurl[0:len(prefix)]tLine)
					#currentLine = ''
					#if (len(cwLines) > 1):
						#for cwNum in range(1, len(cwLines) - 1):
							#result.append(cwLines[cwNum])
						#currentLine = cwLines[-1] + ' '
				#else:
					#currentLine = currentLine + currentWord.strip() + ' '
				#currentWordNum = currentWordNum + 1
			#else:
				#if (currentLineLength > 0):
					##completeLine = currentLine + ' '
					##completeLine = completeLine.strip()
					##result.append(completeLine)
					#result.append(currentLine)
					#currentLine = ''
				#else:
					## Note: if the current word is extremely long, this will cause broken formatting
					## This is intended behaviour, because splitting a single value (e.g. a long filename)
					## across multiple lines makes it extremely frustrating to copy/paste into other commands/windows
					##result.append(currentWord.strip())
					#if ('\n' in currentWord):
						#cwLines = currentWord.splitlines()
						#for cwl in cwLines:
							#result.append(cwl)
					#else:
						#result.append(currentWord)
					#currentWordNum = currentWordNum + 1
				
		## if there's anything left in the buffer, add it now
		#if (len(liblogging.ANSITextFormat.StripANSITermCodes(currentLine)) > 0):
			#result.append(currentLine.strip())
		#return result
		
	@staticmethod
	def BreakTextToLinesByWords(text, lineLength):
		result = []
		allLines = text.splitlines()
		for aLine in allLines:
			allWords = aLine.split(' ')
			currentLine = ''
			currentWordNum = 0
			numWords = len(allWords)
			while (currentWordNum < numWords):
				currentWord = allWords[currentWordNum]
				currentLineLength = len(liblogging.ANSITextFormat.StripANSITermCodes(currentLine))
				wordLength = len(liblogging.ANSITextFormat.StripANSITermCodes(currentWord))
				if ((currentLineLength + wordLength) < lineLength):
					currentLine = currentLine + currentWord.strip() + ' '
					currentWordNum = currentWordNum + 1
				else:
					if (currentLineLength > 0):
						result.append(currentLine)
						currentLine = ''
					else:
						# Note: if the current word is extremely long, this will cause broken formatting
						# This is intended behaviour, because splitting a single value (e.g. a long filename)
						# across multiple lines makes it extremely frustrating to copy/paste into other commands/windows
						#result.append(currentWord.strip())
						result.append(currentWord)
						currentWordNum = currentWordNum + 1
					
			# if there's anything left in the buffer, add it now
			if (len(liblogging.ANSITextFormat.StripANSITermCodes(currentLine)) > 0):
				result.append(currentLine.strip())
		return result
	
	@staticmethod
	def FormatTextAsTable(strings, columnWidths, centerText = False, rightAlign = False):
		result = ''
		numStrings = len(strings)
		numColumnWidths = len(columnWidths)
		if (numStrings != numColumnWidths):
			print 'Error: the number of strings to be formatted as a table must be equivalent to the number of column widths'
			return None
		# split by column width
		textColumns = []
		maxLineCount = 0
		for colNumber in range(0, numColumnWidths):
			newColumn = OutputUtils.BreakTextToLinesByWords(strings[colNumber], columnWidths[colNumber])
			textColumns.append(newColumn)
			if (len(newColumn) > maxLineCount):
				maxLineCount = len(newColumn)
		
		for lineNumber in range(0, maxLineCount):
			for colNumber in range(0, numColumnWidths):
				cellText = ''
				currentColumn = textColumns[colNumber]
				currentColumnWidth = columnWidths[colNumber]
				if (len(currentColumn) > lineNumber):
					cellText = currentColumn[lineNumber]
				if (centerText):
					cellText = OutputUtils.CenterStringWithPaddingChars(currentColumnWidth, ' ', cellText, ' ')
				else:
					if (rightAlign):
						cellText = OutputUtils.PadToLength(cellText, currentColumnWidth, padLeft = True)
					else:
						cellText = OutputUtils.PadToLength(cellText, currentColumnWidth, padLeft = False)
				result = result + cellText
		return result
		
	@staticmethod
	def AppendTemplateFormattedMultiLineText(appendToString, newText, lineLength, formatTemplate):
		result = '' + appendToString
		textLines = OutputUtils.BreakTextToLinesByWords(newText, lineLength)
		for tl in textLines:
			result = result + formatTemplate.format(tl)
		return result
		
		
	@staticmethod
	def PrettyPrintHelpFileSection(terminalWidth, sectionName, fileContent, sectionNameANSITags=[], fileContentANSITags=[], printIfEmpty=False):
		printContent = True
		if ((not (printIfEmpty)) and (fileContent.strip() == '')):
			printContent = False
		if (printContent):
			result = ''
			result = result + '[ ' + liblogging.ANSITextFormat.ANSITextFormatString(sectionName, sectionNameANSITags) + ' ]\n'
			content = ''
			if (terminalWidth > -1):
				padWidth = 2
				contentWidth = terminalWidth - padWidth
				#print 'Debug: "' + fileContent + '"'
				contentLines = OutputUtils.BreakTextToLinesByWords(fileContent, contentWidth)
				for cl in contentLines:
					#print 'Debug: "' + cl + '"'
					content = content + OutputUtils.RepeatString(' ', padWidth)
					content = content + cl + '\n'
				content = liblogging.ANSITextFormat.ANSITextFormatString(content, fileContentANSITags) + '\n'
			else:
				content = fileContent
			result = result + content + '\n'
			print result

	@staticmethod
	def ReplaceCharactersByCharacterNumber(inputString, charNum):
		result = inputString
		hx = '{:02X}'.format(charNum)
		rx = re.compile('\\x' + hx)
		result = rx.sub('[CHR(0x' + hx + ')]', result)
		return result
		
	@staticmethod
	def ReplaceCharactersByCharacterNumberForFilesystemPaths(inputString, charNum):
		result = inputString
		hx = '{:02X}'.format(charNum)
		rx = re.compile('\\x' + hx)
		result = rx.sub('[0x' + hx + ']', result)
		return result
			
	@staticmethod
	def ReplaceNonPrintableCharacters(inputString, replaceNewlineChars = True, replaceTabs = True, useEscapeFormatForCommonChars = True):
		result = inputString
		
		for i in range (0, 9):
			result = OutputUtils.ReplaceCharactersByCharacterNumber(result, i)

		if (replaceTabs):
			if (useEscapeFormatForCommonChars):
				result = result.replace('\t', '\\t')
			else:
				result = OutputUtils.ReplaceCharactersByCharacterNumber(result, 9)

		# newline (0x0A)
		if (replaceNewlineChars):
			if (useEscapeFormatForCommonChars):
				result = result.replace('\n', '\\n')
			else:
				result = OutputUtils.ReplaceCharactersByCharacterNumber(result, 10)

		for i in range (10, 13):
			result = OutputUtils.ReplaceCharactersByCharacterNumber(result, i)

		# carriage return (0x0D)
		if (replaceNewlineChars):
			if (useEscapeFormatForCommonChars):
				result = result.replace('\r', '\\r')
			else:
				result = OutputUtils.ReplaceCharactersByCharacterNumber(result, 13)

		for i in range (14, 32):
			result = OutputUtils.ReplaceCharactersByCharacterNumber(result, i)

		for i in range (127, 256):
			result = OutputUtils.ReplaceCharactersByCharacterNumber(result, i)
			
		return result
		
	@staticmethod
	def ReplaceNonPrintableCharactersForFilesystemPaths(inputString, replacePathSeparatorChars = False, replaceUpperASCIICharacters = False):
		result = inputString
		
		# everything before the space character
		for i in range (0, 32):
			result = OutputUtils.ReplaceCharactersByCharacterNumberForFilesystemPaths(result, i)

		# " - not allowed by Windows
		result = OutputUtils.ReplaceCharactersByCharacterNumberForFilesystemPaths(result, 34)

		# * - not allowed by Windows
		result = OutputUtils.ReplaceCharactersByCharacterNumberForFilesystemPaths(result, 42)

		# : - not allowed by Windows
		result = OutputUtils.ReplaceCharactersByCharacterNumberForFilesystemPaths(result, 58)

		# < and > - not allowed by Windows
		result = OutputUtils.ReplaceCharactersByCharacterNumberForFilesystemPaths(result, 60)
		result = OutputUtils.ReplaceCharactersByCharacterNumberForFilesystemPaths(result, 62)
		
		# ? - not allowed by Windows
		result = OutputUtils.ReplaceCharactersByCharacterNumberForFilesystemPaths(result, 63)
		
		# | - not allowed by Windows
		result = OutputUtils.ReplaceCharactersByCharacterNumberForFilesystemPaths(result, 124)

		if (replacePathSeparatorChars):
			# / - not allowed by Windows
			result = OutputUtils.ReplaceCharactersByCharacterNumberForFilesystemPaths(result, 47)
			# \ - not allowed by Windows
			result = OutputUtils.ReplaceCharactersByCharacterNumberForFilesystemPaths(result, 92)

		if (replaceUpperASCIICharacters):
			for i in range (127, 256):
				result = OutputUtils.ReplaceCharactersByCharacterNumberForFilesystemPaths(result, i)
			
		return result
			
	@staticmethod
	def GetFormattedDateTimeDifference(timediff):
		result = ''
		totalSeconds = timediff.total_seconds()
		# may be a little bit off for purposes of very lengthy times, e.g. off by a day if the length of time was over a year and it was a leap year
		# should be good enough for nearly every purpose I have in mind
		secondsPerYear = 31536000
		secondsPerDay = 86400
		secondsPerHour = 3600
		secondsPerMinute = 60
		if (totalSeconds > secondsPerYear):
			x = divmod(totalSeconds, secondsPerYear)
			numYears = x[0]
			totalSeconds = x[1]
			result = result + '{0} year(s), '.format(numYears)
		if (totalSeconds > secondsPerDay):
			x = divmod(totalSeconds, secondsPerDay)
			numDays = x[0]
			totalSeconds = x[1]
			result = result + '{0} day(s), '.format(numDays)
		if (totalSeconds > secondsPerHour):
			x = divmod(totalSeconds, secondsPerHour)
			numHours = x[0]
			totalSeconds = x[1]
			result = result + '{0} hour(s), '.format(numHours)
		if (totalSeconds > secondsPerMinute):
			x = divmod(totalSeconds, secondsPerMinute)
			numMinutes = x[0]
			totalSeconds = x[1]
			result = result + '{0} minute(s), '.format(numMinutes)
		
		result = result + '{0} second(s)'.format(totalSeconds)

		return result
		
	@staticmethod
	def GetFormattedDateTime(timestamp):
		return timestamp.strftime("%Y-%m-%d @ %H:%M:%S:%f")

	@staticmethod
	def GetFormattedCurrentDateTime():
		return OutputUtils.GetFormattedDateTime(datetime.datetime.now())

	@staticmethod
	def GetFormattedCurrentDateTimeUTC():
		return OutputUtils.GetFormattedDateTime(datetime.datetime.utcnow())

	@staticmethod
	def ActualizeTemplate(template, variables):
		result = template
		# loop until the content is unchanged after a set of replacement operations
		# this is to correctly handle conditions in which one variable refers to another variable
		doneActualizing = False
		while not (doneActualizing):
			initialState = result
			for vName in variables.keys():
				#print 'Template Actualization Key: ' + vName
				if (variables[vName]):
					#print 'Template Actualization Value: ' + str(variables[vName])
					result = result.replace(vName, variables[vName])
				else:
					#print 'Template Actualization Value does not exist'
					result = result.replace(vName, '')
			if (initialState == result):
				doneActualizing = True
		#print "Debug:::Result:" + result
		return result
		
	@staticmethod
	def GetByteCountStringInSIUnits(byteCount):
		result = '{0:.1f} bytes (B)'
		if (byteCount > 1000):
			byteCount = byteCount / 1000
			result = '{0:.1f} kilobytes (KB)'
		if (byteCount > 1000):
			byteCount = byteCount / 1000
			result = '{0:.1f} megabytes (MB)'
		if (byteCount > 1000):
			byteCount = byteCount / 1000
			result = '{0:.1f} gigabytes (GB)'
		if (byteCount > 1000):
			byteCount = byteCount / 1000
			result = '{0:.1f} terabytes (TB)'
		if (byteCount > 1000):
			byteCount = byteCount / 1000
			result = '{0:.1f} petabytes (PB)'
		if (byteCount > 1000):
			byteCount = byteCount / 1000
			result = '{0:.1f} exabytes (EB)'
		if (byteCount > 1000):
			byteCount = byteCount / 1000
			result = '{0:.1f} zettabytes (ZB)'
		if (byteCount > 1000):
			byteCount = byteCount / 1000
			result = '{0:.1f} yottabytes (YB)'

		result = result.format(byteCount)
		return result
		
		
	@staticmethod
	def GetByteCountStringInBinaryUnits(byteCount):
		result = '{0:.1f} bytes (B)'
		if (byteCount > 1024):
			byteCount = byteCount / 1024
			result = '{0:.1f} kibibytes (KiB)'
		if (byteCount > 1024):
			byteCount = byteCount / 1024
			result = '{0:.1f} mebibytes (MiB)'
		if (byteCount > 1024):
			byteCount = byteCount / 1024
			result = '{0:.1f} gibibytes (GiB)'
		if (byteCount > 1024):
			byteCount = byteCount / 1024
			result = '{0:.1f} tebibytes (TiB)'
		if (byteCount > 1024):
			byteCount = byteCount / 1024
			result = '{0:.1f} pebibytes (PiB)'
		if (byteCount > 1024):
			byteCount = byteCount / 1024
			result = '{0:.1f} exbiytes (EiB)'
		if (byteCount > 1024):
			byteCount = byteCount / 1024
			result = '{0:.1f} zebibytes (ZiB)'
		if (byteCount > 1024):
			byteCount = byteCount / 1024
			result = '{0:.1f} yobibytes (YiB)'

		result = result.format(byteCount)
		return result
		
	@staticmethod
	def GenerateOptionOutput(optionName, optionValue, ansiFormatsName, ansiFormatsValue):
		out1 = liblogging.ANSITextFormat.ANSITextFormatString(optionName, ansiFormatsName, False)
		out2 = liblogging.ANSITextFormat.ANSITextFormatString(optionValue, ansiFormatsValue, False)
		return out1 + out2
		
	@staticmethod
	def GenerateRandomChars(length, charString):
		result = ''
		while (len(result) < length):
			charPosition = random.randint(0, len(charString) - 1)
			#print 'Debug: charPosition = {0}'.format(charPosition)
			result = result + charString[charPosition:(charPosition + 1)]
			#print 'Debug: result = "{0}"'.format(result)
		return result
		
	@staticmethod
	def GenerateRandomLowercaseAlphaChars(length):
		return OutputUtils.GenerateRandomChars(length, 'abcdefghijklmnopqrstuvwxyz')
		
	@staticmethod
	def GenerateRandomUppercaseAlphaChars(length):
		return OutputUtils.GenerateRandomChars(length, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')

	@staticmethod
	def GenerateRandomMixedCaseAlphaChars(length):
		return OutputUtils.GenerateRandomChars(length, 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
		
	@staticmethod
	def GenerateRandomNumericChars(length):
		return OutputUtils.GenerateRandomChars(length, '0123456789')
		
	@staticmethod
	def GenerateRandomLowercaseAlphaNumericChars(length):
		return OutputUtils.GenerateRandomChars(length, 'abcdefghijklmnopqrstuvwxyz0123456789')
		
	@staticmethod
	def GenerateRandomUppercaseAlphaNumericChars(length):
		return OutputUtils.GenerateRandomChars(length, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
		
	@staticmethod
	def GenerateRandomMixedCaseAlphaNumericChars(length):
		return OutputUtils.GenerateRandomChars(length, 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')
		
		
	# seriously, I cannot remember Python's bizarre string-slicing syntax
	# it's confusing enough to begin with, and then the developers went and made the part after the colon an absolute position in the string as well?
	# Maybe they should take the fact that there are about a billion questions on StackExchange about how to perform what are a trivial, intuitive
	# operations in EVERY OTHER PROGRAMMING LANGUAGE as a hint that they should build in some helper functions?
	# 
	@staticmethod
	def Right(string, length):
		if (length == 0):
			return ''
		if (length < 0):
			errMsg = "Can't return a negative number ({0}) of characters from a string".format(length)
			raise IndexOutOfBoundsException(errMsg)
		if (len(string) < length):
			errMsg = "The length of the input string is {0}, and so cannot return the rightmost {1} characters".format(len(string), length)
			#print errMsg
			raise IndexOutOfBoundsException(errMsg)
		if (len(string) == length):
			return string
		l = int(length * -1)
		return string[l:]

	@staticmethod
	def RightLess(string, length):
		return OutputUtils.Right(string, len(string) - length)
		
	@staticmethod
	def Left(string, length):
		if (length == 0):
			return ''
		if (length < 0):
			errMsg = "Can't return a negative number ({0}) of characters from a string".format(length)
			raise IndexOutOfBoundsException(errMsg)
		if (len(string) < length):
			errMsg = "The length of the input string is {0}, and so cannot return the leftmost {1} characters".format(len(string), length)
			#print errMsg
			raise IndexOutOfBoundsException(errMsg)
		if (len(string) == length):
			return string
		return string[:length]

	@staticmethod
	def LeftLess(string, length):
		return OutputUtils.Left(string, len(string) - length)
		
	@staticmethod
	def Mid(string, start, length):
		if (length == 0):
			return ''
		if (start < 0):
			errMsg = "Can't return characters from a string starting at a negative offset ({0})".format(start)
			#print errMsg
			raise IndexOutOfBoundsException(errMsg)
		minStringLength = start + length
		if (len(string) < minStringLength):
			errMsg = "The length of the input string is {0}, and so cannot return {1} characters starting at position {2}".format(len(string), length, start)
			#print errMsg
			raise IndexOutOfBoundsException(errMsg)
		if (len(string) == length):
			return string
		return string[start:minStringLength]
	
	# based extremely loosely on http://stackoverflow.com/questions/11103856/re-findall-which-returns-a-dict-of-named-capturing-groups
	# so much easier than just including a built-in collection of named matches in the regex module!
	# also, code which requires reverse-engineering to understand is awesome! I don't use high-level languages because I want the source to be comprehensible!
	# it's so much more fun when every tutorial is a mysterious puzzle!
	# letting the compiler optimize code is for losers! Spending a bunch of time picking apart code to understand it is much more efficient!
	# or better yet, maybe I can just copy/paste in code from the internet without understanding what it does!
	# Thanks Larry Wall!
	@staticmethod
	def GetNamedMatchCollection(regexObject, stringToSearch):
		#return 
		# original unreadable code from Stack Exchange:
		#[
			#dict([
				#[k, i if isinstance(i, str) else i[v-1]]
				#for k,v in regexObject.groupindex.items()
			#])
			#for i in regexObject.findall(stringToSearch)
		#]
		# heavily-modified, readable code with explanation:
		# the result should be a list, and each entry in the list is a hashtable ("dictionary") of named matches from the regex
		# This is so that if I run a regex search with several named match groups on a giant string and get multiple matches
		# I get a distinct collection of named matches for each result
		# e.g. if my input string is "set_01: attrib_01='a', attrib_02='b'; set_02: attrib_01='c', attrib_02='d'; set_03: attrib_01='e', attrib_02='f'"
		# and my regex pattern is "(?P<setid>set_[0-9]{2}): attrib_01='(?P<a1val>[^']*)', attrib_02='(?P<a2val>[^']*)"
		# then I should get a result which is a list whose contents are three hashtables:
		#	hashtable 1:
		#		key = "setid", value = "set_01"
		#		key = "a1val", value = "a"
		#		key = "a2val", value = "b"
		#	hashtable 2:
		#		key = "setid", value = "set_02"
		#		key = "a1val", value = "c"
		#		key = "a2val", value = "d"
		#	hashtable 3:
		#		key = "setid", value = "set_03"
		#		key = "a1val", value = "e"
		#		key = "a2val", value = "f"
		# if my input string is "set_01: attrib_01='a', attrib_02='b'; set_02: attrib_01='c', attrib_02='d'; set_03: attrib_02='f'; set_04: attrib_01='h', attrib_02='i'"
		# and my regex pattern is "(?P<setid>set_[0-9]{2}): (attrib_01='(?P<a1val>[^']*)', )?attrib_02='(?P<a2val>[^']*)"
		# then I should get the following results:
		#	hashtable 1:
		#		key = "setid", value = "set_01"
		#		key = "a1val", value = "a"
		#		key = "a2val", value = "b"
		#	hashtable 2:
		#		key = "setid", value = "set_02"
		#		key = "a1val", value = "c"
		#		key = "a2val", value = "d"
		#	hashtable 3:
		#		key = "setid", value = "set_03"
		#		key = "a1val", value = ""
		#		key = "a2val", value = "f"
		#	hashtable 4:
		#		key = "setid", value = "set_04"
		#		key = "a1val", value = "h"
		#		key = "a2val", value = "i"
		# sounds pretty reasonable and useful, doesn't it?
		result = []
		# iterate through each of the matches that were returned by findall()
		# this is where the values for the hashtables come from
		#print 'Searching: "{0}"'.format(stringToSearch)
		for match in regexObject.findall(stringToSearch):
			# each match = one output hashtable
			newResult = {}
			#print 'Match: "{0}"'.format(match)
			#print 'Group index items: "{0}"'.format(regexObject.groupindex.items())
			# OK, now we have to iterate through the groupindex list of the regular expression pattern
			# because this extremely useful information was discarded by the Python regex findall() method
			# each one of the objects in the items() list is a tuple consisting of the regex group name and its index 
			# in the match, 
			for giGroupName,giGroupIndex in regexObject.groupindex.items():
				#print '"{0}":"{1}"'.format(giGroupName, giGroupIndex)
				groupName = giGroupName
				matchText = None
				# this is slightly more complicated than you might expect, because the way this works is that
				# if there is only one named group, then the match object is just a string with the matching text
				# instead of being a list with one element >=\
				if (isinstance(match, str)):
					#print 'is string'
					matchText = match
				else:
					#print 'is not string'
					matchText = match[giGroupIndex - 1]
				#matchText = match[giGroupIndex - 1]
				#print 'Group name: "{0}"'.format(groupName)
				#print 'Match text: "{0}"'.format(matchText)
				newResult[groupName] = matchText
			result.append(newResult)
		return result
	# PS: NO, I DO NOT WANT TO USE finditer()!!!!!!!!!!!
	# I want the result of the operation to be a collection with a known number of elements!
	# Why would I send code off on its merry way to do something without knowing in advance how many times it would repeat its actions?
	# I mean, unless I wanted to end up with unpredictable code that was hard to support