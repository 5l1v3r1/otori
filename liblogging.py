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
import logging
import re
import time

import liboutput

### begin colourization code based somewhat on code borrowed from Stack Overflow user unutbu
# http://stackoverflow.com/questions/3696430/print-colorful-string-out-to-console-with-python
# has been heavily modified - do not use as a drop-in replacement without expecting consequences


#CODE={
	#'ENDC':0,  # RESET COLOR
	#'BOLD':1,
	#'UNDERLINE':4,
	#'BLINK':5,
	#'INVERT':7,
	#'CONCEALED':8,
	#'STRIKE':9,
	#'GREY30':90,
	#'GREY40':2,
	#'GREY65':37,
	#'GREY70':97,
	#'GREY20_BG':40,
	#'GREY33_BG':100,
	#'GREY80_BG':47,
	#'GREY93_BG':107,
	#'DARK_RED':31,
	#'RED':91,
	#'RED_BG':41,
	#'LIGHT_RED_BG':101,
	#'DARK_YELLOW':33,
	#'YELLOW':93,
	#'YELLOW_BG':43,
	#'LIGHT_YELLOW_BG':103,
	#'DARK_BLUE':34,
	#'BLUE':94,
	#'BLUE_BG':44,
	#'LIGHT_BLUE_BG':104,
	#'DARK_MAGENTA':35,
	#'PURPLE':95,
	#'MAGENTA_BG':45,
	#'LIGHT_PURPLE_BG':105,
	#'DARK_CYAN':36,
	#'AQUA':96,
	#'CYAN_BG':46,
	#'LIGHT_AUQA_BG':106,
	#'DARK_GREEN':32,
	#'GREEN':92,
	#'GREEN_BG':42,
	#'LIGHT_GREEN_BG':102,
	#'BLACK':30,
	#}

class Error(Exception):
	pass
        
ANSIFormatCode={
	'RESET':0,  			# Reset to unformatted text
	# Text formatting (part 1)
	'BOLD':1,
	'FAINT':2,			# Wikipedia: "not widely supported."
					# was named 'GREY40' in the original StackExchange code (?!)
	'ITALIC':3,			# Wikipedia: "not widely supported. Sometimes treated as inverse."
	'UNDERLINE_SINGLE':4,
	'BLINK_SLOW':5,			# Wikipedia: "less than 150 per minute"
	'BLINK_RAPID':6,		# Wikipedia: "MS-DOS ANSI.SYS; 150 per minute or more; not widely supported"
	'IMAGE_NEGATIVE':7,		# Wikipedia: "inverse or reverse; swap foreground and background (reverse video)"
	'CONCEAL':8,			# Wikipedia: "not widely supported."
	'STRIKE':9,			# Wikipedia: "Characters legible, but marked for deletion. Not widely supported."
	'FONT_PRIMARY':10,		# Switch to default font
	'FONT_ALT1':11,			# Switch to alternate font 1
	'FONT_ALT2':12,			# Switch to alternate font 2
	'FONT_ALT3':13,			# Switch to alternate font 3
	'FONT_ALT4':14,			# Switch to alternate font 4
	'FONT_ALT5':15,			# Switch to alternate font 5
	'FONT_ALT6':16,			# Switch to alternate font 6
	'FONT_ALT7':17,			# Switch to alternate font 7
	'FONT_ALT8':18,			# Switch to alternate font 8
	'FONT_ALT9':19,			# Switch to alternate font 9
	'FRAKTUR':20,			# Wikipedia: "hardly ever supported"
	'BOLD_OFF_UNDERLINE_DOUBLE':21,	# Wikipedia: "bold off not widely supported, double underline hardly ever"
	'NORMAL_COLOUR_OR_INTENSITY':22,# Wikipedia: "neither bold nor faint"
	'NOT_ITALIC_OR_FRAKTUR':23,	
	'UNDERLINE_NONE':24,		# supposedly for systems that treat code 21 as a double underline, this will revert that to no underline in addition to code 4
	'BLINK_OFF':25,	
	# #26 is allegedly reserved
	'IMAGE_POSITIVE':27,		# undo the effects of code 7
	'REVEAL':28,			# for systems that support code 8 ("conceal"), undo its effects
	'NOT_CROSSED_OUT':29,
	# Foreground/text colours (ANSI standard)
	'FG_BLACK':30,			# was named 'BLACK' in the original StackExchange code
	'FG_RED':31,			# was named 'DARK_RED' in the original StackExchange code
	'FG_GREEN':32,			# was named 'DARK_GREEN' in the original StackExchange code
	'FG_YELLOW':33,			# was named 'DARK_YELLOW' in the original StackExchange code
	'FG_BLUE':34,			# was named 'DARK_BLUE' in the original StackExchange code
	'FG_MAGENTA':35,		# was named 'DARK_MAGENTA' in the original StackExchange code
	'FG_CYAN':36,			# was named 'DARK_CYAN' in the original StackExchange code
	'FG_WHITE':37,			# was named 'GREY65' in the original StackExchange code
	# #38 is supposedly used by XTerm to allow 8-bit indexed colour use for foreground/text - you can implement that if you want
	'FG_DEFAULT':39,		# switch back to the default colour for foreground/text
	# Background colours (ANSI standard)
	'BG_BLACK':40,			# was named 'GREY20_BG' in the original StackExchange code
	'BG_RED':41,			# was named 'RED_BG' in the original StackExchange code
	'BG_GREEN':42,			# was named 'GREEN_BG' in the original StackExchange code
	'BG_YELLOW':43,			# was named 'YELLOW_BG' in the original StackExchange code
	'BG_BLUE':44,			# was named 'BLUE_BG' in the original StackExchange code
	'BG_MAGENTA':45,		# was named 'MAGENTA_BG' in the original StackExchange code
	'BG_CYAN':46,			# was named 'CYAN_BG' in the original StackExchange code
	'BG_WHITE':47,			# was named 'GREY80_BG' in the original StackExchange code
	# #48 is supposedly used by XTerm to allow 8-bit indexed colour use for background - you can implement that if you want
	'BG_DEFAULT':49,		# switch back to the default colour for background
	# #50 is allegedly reserved
	# Text formatting (part 1)
	'FRAMED':51,	
	'ENCIRCLED':52,	
	'OVERLINED':53,	
	'NOT_FRAMED_OR_ENCIRCLED':54,	
	'NOT_OVERLINED':55,	
	# #56 - #59 are allegedly reserved
	'IDEO_UL_OR_RL':60,		# Wikipedia: "ideogram underline or right side line" / "hardly ever supported"
	'IDEO_D_UL_OR_RL':61,		# Wikipedia: "ideogram double underline or double line on the right side" / "hardly ever supported"
	'IDEO_OL_OR_LL':62,		# Wikipedia: "ideogram overline or left side line" / "hardly ever supported"
	'IDEO_D_OL_OR_LL':63,		# Wikipedia: "ideogram double overline or double line on the left side" / "hardly ever supported"
	'IDEO_STRESS':64,		# Wikipedia: "ideogram stress marking" / "hardly ever supported"
	# gap from 65-89
	# Foreground/text colours - high-intensity (AIXterm)
	'FG_BLACK_HI':90,		# was named 'GREY30' in the original StackExchange code
	'FG_RED_HI':91,			# was named 'RED' in the original StackExchange code
	'FG_GREEN_HI':92,		# was named 'GREEN' in the original StackExchange code
	'FG_YELLOW_HI':93,		# was named 'YELLOW' in the original StackExchange code
	'FG_BLUE_HI':94,		# was named 'BLUE' in the original StackExchange code
	'FG_MAGENTA_HI':95,		# was named 'PURPLE' in the original StackExchange code
	'FG_CYAN_HI':96,		# was named 'AQUA' in the original StackExchange code
	'FG_WHITE_HI':97,		# was named 'GREY70' in the original StackExchange code
	'FG_AIX_98':98,	
	'FG_AIX_99':99,
	# Background colours - high-intensity (AIXterm)
	'BG_BLACK_HI':100,		# was named 'GREY33_BG' in the original StackExchange code
	'BG_RED_HI':101,		# was named 'LIGHT_RED_BG' in the original StackExchange code	
	'BG_GREEN_HI':102,		# was named 'LIGHT_GREEN_BG' in the original StackExchange code
	'BG_YELLOW_HI':103,		# was named 'LIGHT_YELLOW_BG' in the original StackExchange code
	'BG_BLUE_HI':104,		# was named 'LIGHT_BLUE_BG' in the original StackExchange code
	'BG_MAGENTA_HI':105,		# was named 'LIGHT_PURPLE_BG' in the original StackExchange code
	'BG_CYAN_HI':106,		# was named 'LIGHT_AUQA_BG' [sic] in the original StackExchange code
	'BG_WHITE_HI':107,		# was named 'GREY93_BG' in the original StackExchange code
	'BG_AIX_108':108,	
	'BG_AIX_109':109,
	}
	
class ANSITextFormat:

	@staticmethod
	def GetANSITermCode(num):
		return '\033[%sm'%num
		
	@staticmethod
	def StripANSITermCodes(string):
		rx = re.compile(r'\x1b[^m]*m')
		return rx.sub('', string)

	# modified to allow multiple codes to be applied to a single string
	@staticmethod
	def ANSITextFormatString(text, ansiCodeNames, resetAfterString = True):
		result = ''
		for c in ansiCodeNames:
			result = result + ANSITextFormat.GetANSITermCode(ANSIFormatCode[c])
		result = result + text
		if (resetAfterString):
			if (len(ansiCodeNames) > 0):
				result = result + ANSITextFormat.GetANSITermCode(ANSIFormatCode['RESET'])
		return result
		
	@staticmethod
	def GetAllANSICodeNames():
		return ANSIFormatCode.keys()

	@staticmethod
	def GetAllANSICodeNumbers():
		result = []
		for cn in ANSITextFormat.GetAllANSICodeNames():
			result.append(ANSIFormatCode[cn])
		return result

	@staticmethod
	def GetANSICodeNameFromNumber(codeNumber):
		for cn in ANSITextFormat.GetAllANSICodeNames():
			if (codeNumber == ANSIFormatCode[cn]):
				return cn
		return None
		
class LogFormatANSITextFormatCollection:
	def __init__(self):
		self.LevelFormatNames = {
			'DEBUG': [],
			'INFO': [],
			'WARNING': [],
			'ERROR': [],
			'CRITICAL': [],
			}

class EnforcedPlainTextFormatter(logging.Formatter):
	def __init__(self, msg):
		logging.Formatter.__init__(self, msg)

	def format(self, record):
		record = copy.copy(record)
		# attempt to guarantee that *nothing of the host^H^H^H^HANSI codes survives* the logging process, regardless of their origin
		#record.msg = ANSITextFormat.StripANSITermCodes(record.msg)
		# replace non-printable characters
		record.msg = liboutput.OutputUtils.ReplaceNonPrintableCharacters(record.msg)
		return logging.Formatter.format(self, record)
			
class ANSITextFormatter(logging.Formatter):
    # A variant of code found at http://stackoverflow.com/questions/384076/how-can-i-make-the-python-logging-output-to-be-colored

	def __init__(self, msg):
		logging.Formatter.__init__(self, msg)
		self.LevelFormattingLevelName = LogFormatANSITextFormatCollection()
		self.LevelFormattingName = LogFormatANSITextFormatCollection()
		self.LevelFormattingMessage = LogFormatANSITextFormatCollection()
		self.TerminalWidth = -1
		self.LevelNameWidth = 4
		for lfn in self.LevelFormattingLevelName.LevelFormatNames.keys():
			lfnLength = len(lfn)
			if (lfnLength > self.LevelNameWidth):
				self.LevelNameWidth = lfnLength
		#self.LevelNameWidth = self.LevelNameWidth + 1
		self.MessageWidth = (self.TerminalWidth - self.LevelNameWidth)
		
	def SetTerminalWidth(self, terminalWidth):
		self.TerminalWidth = terminalWidth
		self.MessageWidth = (self.TerminalWidth - self.LevelNameWidth)

	def format(self, record):
		record = copy.copy(record)
		levelname = record.levelname
		#levelnameResult = liboutput.OutputUtils.PadToLength(record.levelname + ' ', self.LevelNameWidth, padLeft = True)
		levelnameResult = liboutput.OutputUtils.PadToLength(record.levelname, self.LevelNameWidth, padLeft = True)
		if levelname in self.LevelFormattingLevelName.LevelFormatNames:
			levelnameResult = ANSITextFormat.ANSITextFormatString(levelnameResult, self.LevelFormattingLevelName.LevelFormatNames[levelname])
		record.levelname = levelnameResult
		if levelname in self.LevelFormattingName.LevelFormatNames:
			record.name = ANSITextFormat.ANSITextFormatString(record.name, self.LevelFormattingName.LevelFormatNames[levelname])
		msgResult = record.msg
		if (self.TerminalWidth == -1):
			if levelname in self.LevelFormattingMessage.LevelFormatNames:
				msgResult = ANSITextFormat.ANSITextFormatString(msgResult, self.LevelFormattingMessage.LevelFormatNames[levelname])
		else:
			leftPad = liboutput.OutputUtils.PadToLength(' ', self.LevelNameWidth)
			#leftPad = liboutput.OutputUtils.PadToLength(' ', (self.LevelNameWidth - 2)) + '= '
			if levelname in self.LevelFormattingLevelName.LevelFormatNames:
				leftPad = ANSITextFormat.ANSITextFormatString(leftPad, self.LevelFormattingLevelName.LevelFormatNames[levelname])
			messageLines = liboutput.OutputUtils.BreakTextToLinesByWords(msgResult, (self.MessageWidth - 1))
			msgResult = liboutput.OutputUtils.PadToLength(' ' + messageLines[0].strip(), self.MessageWidth)
			if levelname in self.LevelFormattingMessage.LevelFormatNames:
				msgResult = ANSITextFormat.ANSITextFormatString(msgResult, self.LevelFormattingMessage.LevelFormatNames[levelname])
			msgResult = msgResult + '\n'
			for lineNum in range(1, len(messageLines)):
				newLine = liboutput.OutputUtils.PadToLength(' ' + messageLines[lineNum].strip(), self.MessageWidth)
				if (newLine.strip() != ''):
					if levelname in self.LevelFormattingMessage.LevelFormatNames:
						newLine = ANSITextFormat.ANSITextFormatString(newLine, self.LevelFormattingMessage.LevelFormatNames[levelname])
					newLine = leftPad + newLine
					msgResult = msgResult + newLine + '\n'
					
#			if levelname in self.LevelFormattingMessage.LevelFormatNames:
#				msgResult = ANSITextFormat.ANSITextFormatString(msgResult, self.LevelFormattingMessage.LevelFormatNames[levelname])
		if (msgResult[-1] == '\n'):
			msgResult = msgResult[:-1]
		record.msg = msgResult
		return logging.Formatter.format(self, record)

### end heavily-modified version of formatting code borrowed from Stack Overflow user unutbu

class LogLevelException(Error):
    def __init__(self, msg):
        self.msg = msg
        
class LogLevel:
	def __init__(self):
		self.Name = 'INFO'
		self.Level = logging.INFO
		
	def SetFromString(self, levelString):
		s = levelString.strip().upper()
		foundLevel = False
		if (s == 'NONE'):
			self.Level = logging.CRITICAL
			foundLevel = True
		if (s == 'DEBUG'):
			self.Level = logging.DEBUG
			foundLevel = True
		if (s == 'INFO'):
			self.Level = logging.INFO
			foundLevel = True
		if (s == 'WARNING'):
			self.Level = logging.WARNING
			foundLevel = True
		if (s == 'ERROR'):
			self.Level = logging.ERROR
			foundLevel = True
		if (s == 'CRITICAL'):
			self.Level = logging.CRITICAL
			foundLevel = True
		
		if (foundLevel):
			self.Name = s
		else:
			errMsg = 'Unrecognized log level: "' + levelString + '"'
			#print errMsg
			raise LogLevelException()
		
	@staticmethod
	def CreateFromString(levelString):
		result = LogLevel()
		result.SetFromString(levelString)
		return result

class MultiLogger:
	def __init__(self):
		self.loggers = []

	def handleFailedLoggerCall(self, message):
		print 'Error: could not send the message "' + message + '" to a logger'
		
	def debug(self, message):
		if (self.loggers):
			for logger in self.loggers:
				try:
					logger.debug(message)
				except:
					self.handleFailedLoggerCall(message)
					
	def info(self, message):
		if (self.loggers):
			for logger in self.loggers:
				try:
					logger.info(message)
				except:
					self.handleFailedLoggerCall(message)

	def warning(self, message):
		if (self.loggers):
			for logger in self.loggers:
				try:
					logger.warning(message)
				except:
					self.handleFailedLoggerCall(message)

	def error(self, message):
		if (self.loggers):
			for logger in self.loggers:
				try:
					logger.error(message)
				except:
					self.handleFailedLoggerCall(message)

	def critical(self, message):
		if (self.loggers):
			for logger in self.loggers:
				try:
					logger.critical(message)
				except:
					self.handleFailedLoggerCall(message)
	
# Borrowed from http://docs.python.org/2/library/datetime.html
# don't know why this isn't built into Python...
class LocalTimezone(datetime.tzinfo):

	def utcoffset(self, dt):
		if self._isdst(dt):
			return DSTOFFSET
		else:
			return STDOFFSET

	def dst(self, dt):
		if self._isdst(dt):
			return DSTDIFF
		else:
			return ZERO

	def tzname(self, dt):
		return _time.tzname[self._isdst(dt)]

	def _isdst(self, dt):
		tt = (dt.year, dt.month, dt.day,
		dt.hour, dt.minute, dt.second,
		dt.weekday(), 0, 0)
		stamp = _time.mktime(tt)
		tt = _time.localtime(stamp)
		return tt.tm_isdst > 0