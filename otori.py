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

import argparse
import datetime
import httplib
import logging
import math
import os
import re
import subprocess
import sys
import time

import libfileio
import liblogging
import libotori
import liboutput
import libswamm
import libxxeexploits
import xxeexploitmodules

__author__ = 'Ben Lincoln - http://www.beneaththewaves.net/'

	

def GetVersion():
	return '0.3 - 2014-07-20'

def GetProgramName():
	return 'On The Outside, Reaching In ("OTORI") version {0}'.format(GetVersion())

def GetLogoFile(subdirectory):
	fullPath = libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/data/otori/banners/{0}'.format(subdirectory))
	#print fullPath
	selector = libfileio.RandomFileSelector(fullPath)
	filePath = selector.GetRandomEntry()
	if not (filePath):
		return None
	result = libfileio.FileReader.getFileAsList(filePath)
	return result
	
def GetProgramLogo(terminalWidth):
	result = []
	gotLogo = False
	if (terminalWidth < 80):
		# no logo for terminal width less than 80 columns
		gotLogo = True
	# for other terminal widths, use appropriate-sized logo
	sizes = [80, 120, 160, 200]
	for s in range(0, len(sizes)):
		if not (gotLogo):
			if (s == (len(sizes) - 1)):
				gotLogo = True
				result = GetLogoFile(str(sizes[s]))
			else:
				if (terminalWidth < sizes[s + 1]):
					gotLogo = True
					result = GetLogoFile(str(sizes[s]))
	return result

	
def getAboutString(terminalWidth, useANSIFormatting):
	warningBeestripeFormatting = ['BG_BLACK', 'FG_YELLOW', 'BOLD']
	warningHeaderFormatting = ['BG_BLACK', 'FG_RED', 'BOLD']
	warningTextFormatting = ['BG_BLACK', 'FG_YELLOW']
	titleTextFormatting = ['BG_BLACK', 'FG_GREEN', 'BOLD']
	titleSubTextFormatting = ['BG_BLACK', 'FG_GREEN', 'FAINT']
	titleCreedFormatting = ['BG_BLACK', 'FG_MAGENTA', 'FAINT']
	if not (useANSIFormatting):
		warningBeestripeFormatting = []
		warningHeaderFormatting = []
		warningTextFormatting = []
		titleTextFormatting = []
		titleSubTextFormatting = []
		titleCreedFormatting = []
	result = liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.CenterStringWithPaddingChars(terminalWidth, ' ', '  ', ' '), titleTextFormatting)
	if (useANSIFormatting):
		pgl = GetProgramLogo(terminalWidth)
		for pglLine in pgl:			
			#result = result + liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.CenterStringWithPaddingChars(terminalWidth, ' ', pglLine, ' '), titleTextFormatting)
			result = result + liboutput.OutputUtils.CenterStringWithPaddingChars(terminalWidth, ' ', pglLine, ' ')
			result = result + '\n'	
	result = result + liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.CenterStringWithPaddingChars(terminalWidth, ' ', GetProgramName(), ' '), titleTextFormatting)
	result = result + '\n'
	programDescription = 'An XML external entity ("XXE") capability-maximizing, bounty-harvesting utility'
	result = result + liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.CenterStringWithPaddingChars(terminalWidth, ' ', programDescription, ' '), titleSubTextFormatting)
	result = result + '\n'
	#result = result + 'A utility for lawfully and ethically maximizing the capabilities and harvesting the bounties of XML external entities ("XXE")\n'
	#result = result + '==> For lawful and ethical use only <==\n'
	#result = result + liboutput.OutputUtils.CenterString(terminalWidth, '==[ For use only in ways which are both lawful and ethical ]==')
	programCreed = '==[ For use only in ways which are both lawful and ethical ]=='
	result = result + liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.CenterStringWithPaddingChars(terminalWidth, ' ', programCreed, ' '), titleCreedFormatting)
	result = result + liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.CenterStringWithPaddingChars(terminalWidth, ' ', '  ', ' '), titleCreedFormatting)
	result = result + '\n\n'
	result = result + liboutput.OutputUtils.CenterString(terminalWidth, 'Copyright 2014 Ben Lincoln')
	result = result + '\n'
	result = result + liboutput.OutputUtils.CenterString(terminalWidth, 'http://www.beneaththewaves.net/Software/On_The_Outside_Reaching_In.html')
	result = result + '\n'
	result = result + liboutput.OutputUtils.CenterString(terminalWidth, 'Visit http://www.beneaththewaves.net/Software/ for detailed tutorials')
	result = result + '\n'
	result = result + liboutput.OutputUtils.CenterString(terminalWidth, 'Released under version 3 of the GPL - see the accompanying LICENSE.txt file')
	result = result + '\n\n'
	dangerBlock = ''
	dangerHeader = liblogging.ANSITextFormat.ANSITextFormatString('[  ', warningBeestripeFormatting)
	dangerHeader = dangerHeader + liblogging.ANSITextFormat.ANSITextFormatString('WARNING', warningHeaderFormatting)
	dangerHeader = dangerHeader + liblogging.ANSITextFormat.ANSITextFormatString('  ]', warningBeestripeFormatting)
	dangerBeeStripeLeft = liblogging.ANSITextFormat.ANSITextFormatString('\\', warningBeestripeFormatting)
	dangerBeeStripeRight = liblogging.ANSITextFormat.ANSITextFormatString('/', warningBeestripeFormatting)
	dangerBlock = dangerBlock + liboutput.OutputUtils.CenterStringWithPaddingChars(terminalWidth, dangerBeeStripeLeft, dangerHeader, dangerBeeStripeRight)
	dangerBlock = dangerBlock + '\n'

	dangerStringBodyWidth = terminalWidth - 6

	templateDangerString = dangerBeeStripeLeft + liblogging.ANSITextFormat.ANSITextFormatString('  {0:' + str(dangerStringBodyWidth) + '}  ', warningTextFormatting) + dangerBeeStripeRight + '\n'
	dangerBlock = dangerBlock + templateDangerString.format(' ')

	
	dangerString = 'Your government, employer, or another entity may restrict or prohibit the use (or even possession) of this type of tool. The penalties for violating such laws or policies can be severe. Compliance with any such laws or policies is _your_ responsibility. If you are unsure whether or not you are allowed to use this tool specifically, or this class of tool in general, you should discontinue its use until you have determined that you are allowed to use it.'
	dangerBlock = liboutput.OutputUtils.AppendTemplateFormattedMultiLineText(dangerBlock, dangerString, dangerStringBodyWidth, templateDangerString)

	
	dangerBlock = dangerBlock + templateDangerString.format(' ')
	dangerString = 'While this tool has been engineered with safe operation in mind, the type of work it performs is inherently dangerous. Its use may result in loss of data, instability, or other negative effects on both your own system as well as any target systems. It is strongly recommended that you back up and/or snapshot all systems involved in its use (including your own) before each use, and revert to the pre-testing state after testing has completed. If you are not prepared to be held personally responsible for any potential results, you should not use this tool.'
	
	dangerBlock = liboutput.OutputUtils.AppendTemplateFormattedMultiLineText(dangerBlock, dangerString, dangerStringBodyWidth, templateDangerString)
	dangerBlock = dangerBlock + templateDangerString.format(' ')
	dangerBlock = dangerBlock + liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.CenterStringWithPaddingChars(terminalWidth, '\\', '                                        ', '/'), warningBeestripeFormatting)
	
	result = result + dangerBlock
	result = result + '\n'
	return result

def GenerateOptionOutputForRetainDiscard(multiLogger, optionName, discard, ansiFormatsOutputHeaders, ansiFormatsOptions):
	d = 'retained'
	if (discard):
		d = 'discarded'
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput(optionName, d, ansiFormatsOutputHeaders, ansiFormatsOptions))

def main():

	useANSIFormatting = True
	# have to put this right at the beginning because some of the default output is colour-formatted
	if ("--no-ansi" in sys.argv):
		useANSIFormatting = False

	# formatting collections
	ansiFormatsLoggingLevelName = liblogging.LogFormatANSITextFormatCollection()
	ansiFormatsLoggingName = liblogging.LogFormatANSITextFormatCollection()
	ansiFormatsLoggingMessage = liblogging.LogFormatANSITextFormatCollection()
	
	# individual sets of formatting options
	ansiFormatsOutputHeaders = []
	ansiFormatsModuleListHeaders = []
	ansiFormatsModuleListUID = []
	ansiFormatsModuleListDescription = []
	ansiFormatsOptions = []
	ansiFormatsOutputDetails = []
	ansiFormatsModuleDetailsHeader = []
	ansiFormatsModuleDetailsContent = []
	ansiFormatsModuleParametersHeader = []
	ansiFormatsModuleParametersParameterName = []
	ansiFormatsModuleParametersParameterDescription = []
		
	if (useANSIFormatting):
		# formatting for log level text ("DEBUG", "INFO", etc)
		ansiFormatsLoggingLevelName.LevelFormatNames = {
			'DEBUG': ['FG_WHITE', 'BG_BLUE', 'BOLD'],
			'INFO': ['FG_WHITE', 'BG_BLACK', 'BOLD'],
			'WARNING': ['FG_WHITE', 'BG_YELLOW', 'BOLD'],
			'ERROR': ['FG_WHITE', 'BG_RED', 'BOLD'],
			'CRITICAL': ['FG_BLACK', 'BG_RED_HI', 'BOLD'],
			}
		# formatting for log "name" field
		ansiFormatsLoggingName.LevelFormatNames = {
			'DEBUG': ['FG_BLUE', 'BG_WHITE_HI'],
			'INFO': ['FG_BLACK', 'BG_WHITE_HI'],
			'WARNING': ['FG_YELLOW', 'BG_WHITE_HI'],
			'ERROR': ['FG_RED', 'BG_WHITE_HI'],
			'CRITICAL': ['FG_RED_HI', 'BG_WHITE_HI'],
			}
		# formatting for log message field
		ansiFormatsLoggingMessage.LevelFormatNames = {
			'DEBUG': ['FG_BLUE', 'BG_WHITE_HI'],
			'INFO': ['FG_BLACK', 'BG_WHITE_HI'],
			'WARNING': ['FG_YELLOW', 'BG_BLACK'],
			'ERROR': ['FG_RED', 'BG_BLACK'],
			'CRITICAL': ['FG_RED_HI', 'BG_BLACK', 'BOLD'],
			}
		ansiFormatsOutputHeaders = ['BOLD']
		ansiFormatsModuleListHeaders = ['BG_MAGENTA', 'FG_WHITE_HI', 'BOLD']
		ansiFormatsModuleListUID = ['BOLD']
		ansiFormatsModuleListDescription = []
		ansiFormatsOptions = ['FG_MAGENTA', 'FAINT']
		ansiFormatsOutputDetails = ['FG_CYAN', 'FAINT']
		ansiFormatsModuleDetailsHeader = ['FG_BLUE_HI', 'BOLD']
		ansiFormatsModuleDetailsContent = []
		ansiFormatsModuleParametersHeader = ['FG_RED', 'FAINT']
		ansiFormatsModuleParametersParameterName = ['FG_GREEN', 'FAINT']
		ansiFormatsModuleParametersParameterDescription = []

	twidth = liboutput.OutputUtils.GetTerminalWidth()
	if (twidth < 40):
		twidth = 40
		
	multiLogger = liblogging.MultiLogger()

	logFormatStringConsole = '%(levelname)s%(message)s'
	logFormatStringFile = '%(asctime)s\t%(levelname)s\t%(message)s\t[%(pathname)s, line %(lineno)s]'
	
	consoleLogger=logging.getLogger(__name__ + '-Console')
	consoleLogger.setLevel(logging.INFO)
	console = logging.StreamHandler()
	consoleFormatter = liblogging.ANSITextFormatter(logFormatStringConsole)
	consoleFormatter.SetTerminalWidth(twidth)
	consoleFormatter.LevelFormattingLevelName = ansiFormatsLoggingLevelName
	consoleFormatter.LevelFormattingName = ansiFormatsLoggingName
	consoleFormatter.LevelFormattingMessage = ansiFormatsLoggingMessage
	console.setFormatter(consoleFormatter)
	consoleLogger.addHandler(console)
	
	multiLogger.loggers.append(consoleLogger)
	
	templateAboutString = '{0:' + str(twidth) + '}'
	
	print getAboutString(twidth, useANSIFormatting)
	
	parser = argparse.ArgumentParser(description="")
	parser.add_argument("--usage", help="display detailed help/usage/about instructions", action="store_true")
	parser.add_argument("--list", help="list all available XXE modules", action="store_true")
	parser.add_argument("--details", help="display detailed information about a particular XXE module", action="store_true")
	parser.add_argument("--module", metavar='MODULE_ID', help="use the specified XXE module ID")
	opmodes = parser.add_mutually_exclusive_group()
	opmodes.add_argument("--clone", help="clone the remote target(s) to the local filesystem", action="store_true")
	#opmodes.add_argument("--test", help="tests whether the given configuration operates correctly", action="store_true")
	#opmodes.add_argument("--portscan", help="perform a limited portscan/banner-grabbing operation", action="store_true")
	#opmodes.add_argument("--xxeproxy", help="act as an extremely limited HTTP proxy server via the XXE channel", action="store_true")
	opmodes.add_argument("--test", help="this option is not currently implemented or supported", action="store_true")
	opmodes.add_argument("--portscan", help="this option is not currently implemented or supported", action="store_true")
	opmodes.add_argument("--xxeproxy", help="this option is not currently implemented or supported", action="store_true")

	opmodes.add_argument("--dos-lulz", dest='doslulz', help="attempt to create a denial-of-service condition using the 'billion lolz' technique", action="store_true")
	opmodes.add_argument("--dos-quad", dest='dosquad', help="attempt to create a denial-of-service condition using the 'quadratic blowup' technique", action="store_true")
	parser.add_argument("--module-options", dest='moduleoptions', default=[], help="one or more options which are passed to the selected module - the first (sometimes only) option is generally the vulnerable URL to target", action='append', nargs='+')
	parser.add_argument("--swamm-url-base", dest='swammURLBase', metavar='URL', help="for modules and modes which require the use of She Wore A Mirrored Mask, use this URL as the base URL for creating other URLs")
	parser.add_argument("--swamm-url-read", dest='swammURLRead', metavar='URL', help="for modules and modes which require the use of She Wore A Mirrored Mask, use this URL for read operations")
	parser.add_argument("--swamm-url-write", dest='swammURLWrite', metavar='URL', help="for modules and modes which require the use of She Wore A Mirrored Mask, use this URL for write operations")
	parser.add_argument("--swamm-url-append", dest='swammURLAppend', metavar='URL', help="for modules and modes which require the use of She Wore A Mirrored Mask, use this URL for append operations")
	parser.add_argument("--swamm-url-delete", dest='swammURLDelete', metavar='URL', help="for modules and modes which require the use of She Wore A Mirrored Mask, use this URL for delete operations")
	parser.add_argument("--swamm-url-store-add", dest='swammURLStoreAdd', metavar='URL', help="for modules and modes which require the use of She Wore A Mirrored Mask, use this URL for stored request/response add operations")
	parser.add_argument("--swamm-url-store-delete", dest='swammURLStoreDelete', metavar='URL', help="for modules and modes which require the use of She Wore A Mirrored Mask, use this URL for stored request/response delete operations")
	targetspec = parser.add_mutually_exclusive_group()
	targetspec.add_argument("--singleuri", metavar='REQUESTED_URI', help="attempt to retrieve the contents of a single URI (e.g. file:///var/log/messages)")
	targetspec.add_argument("--exacturilist", metavar='PATH_TO_EXACT_URI_LIST_FILE', help="read each line in PATH_TO_EXACT_URI_LIST_FILE as a URI from which the contents should be retrieved - will not recurse through them, even if they are directory listings")
	targetspec.add_argument("--rooturi", metavar='REQUESTED_ROOT_URI', help="attempt to retrieve a URI containing a directory listing, and follow its branches recursively")
	targetspec.add_argument("--rooturilist", metavar='PATH_TO_ROOT_URI_LIST_FILE', help="read each line in PATH_TO_ROOT_URI_LIST_FILE as a root URI to begin recursion from")
	parser.add_argument("--outputbase", metavar='BASE_OUTPUT_PATH', help="the base local directory into which any retrieved data should be replicated", default="./output/")
	parser.add_argument("--uriblacklist", metavar='PATH_TO_TARGET_URI_BLACKLIST_FILE', help="use a list of regular expressions to blacklist certain URIs (e.g. /sys on Linux/Unix)")
	existingfiles = parser.add_mutually_exclusive_group()
	existingfiles.add_argument("--preserve", help="when downloading content, if the local file already exists, preserve the existing file", action="store_true")
	existingfiles.add_argument("--overwrite", help="when downloading content, if the local file already exists, overwrite it", action="store_true")
	existingfiles.add_argument("--version", help="when downloading content, if the local file already exists, create a new file with a version number appended so that both are stored", action="store_true")
	#parser.add_argument("--tarad", help="when downloading content, test every result for being a directory listing (as opposed to a file) by attempting to download files whose paths correspond with lines in the result - the default behaviour is to attempt to determine this more intelligently", action="store_true")
	parser.add_argument("--noerrorfiles", help="when downloading content, if a request generates an error, do not store the result in a file", action="store_true")
	parser.add_argument("--noemptyfiles", help="when downloading content, if a zero-byte file is downloaded, do not store it", action="store_true")
	parser.add_argument("--nowhitespacefiles", help="when downloading content, if --noemptyfiles is specified, consider files which contain only whitespace as 'empty'", action="store_true")
	parser.add_argument("--noemptydirs", help="when downloading content, if an empty directory is downloaded, delete it", action="store_true")
	parser.add_argument("--maxdepth", type=int, metavar='D', help="when using modes involving recursion, limit the recursion to this many hops down any given path", default=20)
	parser.add_argument("--retries", type=int, metavar='R', help="if a given request fails, retry this many times before giving up (does not apply to permission- or data-related failures)", default=0)
	parser.add_argument("--request-timeout", dest='requesttimeout', type=int, metavar='SECONDS', help="wait this long for each request before giving up", default=60)
	parser.add_argument("--request-waittime", dest='requestwaittime', type=int, metavar='WAIT_MILLISECONDS', help="wait this long between each request", default=0)
	parser.add_argument("--request-waittime-window", dest='requestwaittimewindow', type=int, metavar='WINDOW_MILLISECONDS', help="vary the request wait time by this many milliseconds, centered on the base request wait time (to help avoid looking like an automated process)", default=0)
	parser.add_argument("--http-user-agent", dest='httpUserAgent', metavar='USER_AGENT', help="for HTTP-based modules, send this string as the User-Agent value when making HTTP requests - if this option is not specified, a random value will be selected from the bundled configuration files")
	parser.add_argument("--http-cookie", dest='httpCookie', metavar='COOKIE_STRING', help="for HTTP-based modules, if this value is specified, it will be sent as the content of the Cookie HTTP header with each request")
	#parser.add_argument("--xxep-storeallresults", help="when acting as an XXE proxy, replicate all retrieved content locally, as if it had been spidered using the recursion option", action="store_true")
	#parser.add_argument("--xxep-getforallmethods", help="when acting as an XXE proxy, replace all other HTTP methods with GET (if this option is not selected, those methods will return an error)", action="store_true")
	#parser.add_argument("--xxep-movebodyparams", help="when acting as an XXE proxy, move parameters sent in the body of client requests to the URL (IE attempt to translate them to GET parameters)", action="store_true")
	#parser.add_argument("--xxep-suppressproxymessages", help="when acting as an XXE proxy, if an error occurs, return a generic HTTP response code instead of an OTORI-specific message page", action="store_true")
	parser.add_argument("--xxep-storeallresults", help="this option is not currently implemented or supported", action="store_true")
	parser.add_argument("--xxep-getforallmethods", help="this option is not currently implemented or supported", action="store_true")
	parser.add_argument("--xxep-movebodyparams", help="this option is not currently implemented or supported", action="store_true")
	parser.add_argument("--xxep-suppressproxymessages", help="this option is not currently implemented or supported", action="store_true")
	
	parser.add_argument("--dos-lulz-base", dest='doslulzbase', type=int, metavar='LB', help="in --dos-lulz mode, use this many lulz as the base (minimum: 1, default: 10)", default=10)
	parser.add_argument("--dos-lulz-exp", dest='doslulzexp', type=int, metavar='LE', help="in --dos-lulz mode, use this many tiers of lulz (minimum: 2, default: 9)", default=9)
	parser.add_argument("--dos-quad-base", dest='dosquadbase', type=int, metavar='LB', help="in --dos-quad mode, use this many copies of the string as the base (minimum: 1, default: 10000)", default=10000)
	parser.add_argument("--dos-quad-mult", dest='dosquadmult', type=int, metavar='LE', help="in --dos-quad mode, expand the base value this many times in memory on the target system (minimum: 1, default: 100000)", default=100000)
	parser.add_argument("--dos-string", dest='dosstring', metavar='DOS_STRING', help="in --dos-lulz and --dos-quad mode, use this string as the one which will be repeated in memory (LB^LE for --dos-lulz and QM*QB for --dos-quad) on the target system (default: -- Summon the Lulz --)", default="-- Summon the Lulz --")
	parser.add_argument("--console-verbosity", dest='consoleVerbosity', choices=['debug', 'info', 'warning', 'error', 'critical'], help="set the level of verbosity for console output", default='info')
	parser.add_argument("--log-verbosity", dest='logfileVerbosity', choices=['debug', 'info', 'warning', 'error', 'critical'], help="set the level of verbosity for log file output (only used if --log is specified)", default='info')
	parser.add_argument("--log", dest='logfilePath', metavar='LOG_FILE_PATH', help="specify an optional file to which console-type messages should be logged - will be appended to if it already exists")
	parser.add_argument("--reportfile", metavar='FILE_PATH', help="the path to which a file should be written containing tab-delimited results for any downloads attempted")
	parser.add_argument("--no-ansi", dest='noansi', help='DO NOT use ANSI codes to make the console output look awesome and amazing and like you are a "l33+" super-hacker hacking some radical "zero-days" and "pwning" some "boxes"', action="store_true")
	
	args = parser.parse_args()

	consoleVerbosity = 'INFO'
	logfileVerbosity = 'NONE'

	if (args.consoleVerbosity):
		consoleVerbosity = args.consoleVerbosity

	consoleLogLevel = liblogging.LogLevel.CreateFromString(consoleVerbosity)
	multiLogger.loggers[0].setLevel(consoleLogLevel.Level)

	logfileLogLevel = liblogging.LogLevel.CreateFromString(logfileVerbosity)
	usingLogFile = False
	if (args.logfilePath):
		logfileVerbosity = 'INFO'
		if (args.logfileVerbosity):
			logfileVerbosity = args.logfileVerbosity
		logfileLogLevel = liblogging.LogLevel.CreateFromString(logfileVerbosity)
		fileLogger=logging.getLogger(__name__ + '-File Log')
		fileLogger.setLevel(logfileLogLevel.Level)
		try:
			fileLoggingHandler = logging.FileHandler(args.logfilePath, 'a')
			fileFormatter = liblogging.EnforcedPlainTextFormatter(logFormatStringFile)
			fileLoggingHandler.setFormatter(fileFormatter)
			fileLogger.addHandler(fileLoggingHandler)
			
			multiLogger.loggers.append(fileLogger)
			usingLogFile = True
		except:
			multiLogger.error('Could not create or append to the log file path "' + args.logfilePath + '" - output will be to console only')

	startTimestampUTC = datetime.datetime.utcnow()
	startTimestamp = datetime.datetime.now()
	#multiLogger.info('Execution beginning: {0}'.format(liboutput.OutputUtils.GetFormattedDateTime(startTimestamp)))
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Execution beginning: ', liboutput.OutputUtils.GetFormattedDateTime(startTimestamp), ansiFormatsOutputHeaders, ansiFormatsOutputDetails))
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Console verbosity: ', consoleLogLevel.Name, ansiFormatsOutputHeaders, ansiFormatsOptions))
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Log file verbosity: ', logfileLogLevel.Name, ansiFormatsOutputHeaders, ansiFormatsOptions))
	if (usingLogFile):
		multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Log file: ', args.logfilePath, ansiFormatsOutputHeaders, ansiFormatsOptions))
			
	if (args.usage):
		parser.print_help()
		print libfileio.FileReader.getFileAsString(libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/data/helptext.txt'))
		sys.exit(0)

	if (args.noansi):
		multiLogger.warning('ANSI text formatting has been disabled. Two points have been removed from your license to "hack the Gibson".')
		
	mods = xxeexploitmodules.XXEExploitModuleEnumerator.getModules()
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Modules available: ', str(len(mods)), ansiFormatsOutputHeaders, ansiFormatsOutputDetails))
	if (args.list):
		
		print liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.CenterStringWithPaddingChars(twidth, ' ', '- Available Modules -', ' '), ansiFormatsOutputHeaders)
		
		col1Width = 24
		col2Width = twidth - col1Width
		columnWidths = [col1Width, col2Width]

		#headerLine = liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.PadToLength("Module ID", col1Width), ansiFormatsModuleListHeaders)
		#headerLine = headerLine + liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.PadToLength("Short Description", col2Width), ansiFormatsModuleListHeaders)
		#print headerLine
		
		headerStrings = ['Module ID', 'Short Description']
		
		headerBlock = liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.FormatTextAsTable(headerStrings, columnWidths, centerText = True), ansiFormatsModuleListHeaders)
		print headerBlock
		#for m in mods:
			#mUID = liblogging.ANSITextFormat.ANSITextFormatString(m.uniqueID, ansiFormatsModuleListUID)
			#mName = liblogging.ANSITextFormat.ANSITextFormatString(m.name, ansiFormatsModuleListDescription)
			#mLine = liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.PadToLength(mUID, col1Width), ansiFormatsModuleListUID)
			#mLine = mLine + liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.PadToLength(mName, col2Width), ansiFormatsModuleListDescription)
			#print mLine
			
		for m in mods:
			modStrings = []

			modStrings.append(liblogging.ANSITextFormat.ANSITextFormatString(m.uniqueID, ansiFormatsModuleListUID))
			modStrings.append(liblogging.ANSITextFormat.ANSITextFormatString(m.name, ansiFormatsModuleListDescription))
			modBlock = liboutput.OutputUtils.FormatTextAsTable(modStrings, columnWidths)
			print modBlock
			print ''
		sys.exit(0)
	
	if not (args.module):
		multiLogger.critical('All operating modes except --help, --usage, and --list must specify a module ID using the --module option (e.g. --module "CVE-2013-6407-DARH")')
		sys.exit(1)

	activeModule = mods[0]
	foundModule = False
	for m in mods:
		if (m.uniqueID == args.module):
			multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Using module: ', m.uniqueID, ansiFormatsOutputHeaders, ansiFormatsOptions))
			activeModule = m
			foundModule = True
	if not (foundModule):
		multiLogger.critical('Could not find a module with ID "' + args.module + '"')
		sys.exit(1)
		
	activeModule.MultiLogger = multiLogger
		
	if (args.details):
		liboutput.OutputUtils.PrettyPrintHelpFileSection(twidth, 'Module Overview', activeModule.GetDataOverview(), ansiFormatsModuleDetailsHeader, ansiFormatsModuleDetailsContent, True)
		modRequiredParms = activeModule.GetRequiredParameters()
		modOptionalParms = activeModule.GetOptionalParameters()
		numRequiredParms = len(modRequiredParms)
		numOptionalParms = len(modOptionalParms)
		numParms = numRequiredParms + numOptionalParms
		parmDefinitionString = ''
		if (numOptionalParms == 0):
			'This module accepts '  + str(numParms) 
			if (numParms > 1):
				parmDefinitionString = parmDefinitionString + ' parameters. All ' + str(numParms) + ' are required.'
			else:
				parmDefinitionString = parmDefinitionString + ' parameter. This single parameter is required.'
		else:
			parmDefinitionString = 'This module accepts a total of ' + str(numParms)
			if (numParms > 1):
				parmDefinitionString = parmDefinitionString + ' parameters. '
			else:
				parmDefinitionString = parmDefinitionString + ' parameter. '
			if (numRequiredParms == 0):
				# seems unlikely...
				parmDefinitionString = parmDefinitionString + 'There are no required parameters. '
			if (numRequiredParms == 1):
				parmDefinitionString = parmDefinitionString + 'The first parameter is required. '
			if (numRequiredParms > 1):
				parmDefinitionString = parmDefinitionString + 'The first ' + str(numRequiredParms) + ' parameters are required. '
			if (numOptionalParms == 1):
				parmDefinitionString = parmDefinitionString + 'One optional parameter may also be specified.'
			if (numOptionalParms > 1):
				parmDefinitionString = parmDefinitionString + str(numOptionalParms) + ' optional parameters may also be specified.'
		
		parmDefinitionString = parmDefinitionString + '\n'
		if (len(modRequiredParms) > 0):
			parmDefinitionString = parmDefinitionString + '\n'
			parmDefinitionString = parmDefinitionString + liblogging.ANSITextFormat.ANSITextFormatString('- Required Parameters -', ansiFormatsModuleParametersHeader) + '\n\n'
			for mrp in modRequiredParms:
				parmDefinitionString = parmDefinitionString + liblogging.ANSITextFormat.ANSITextFormatString(mrp.Name, ansiFormatsModuleParametersParameterName) + '\n'
				parmDefinitionString = parmDefinitionString + liblogging.ANSITextFormat.ANSITextFormatString(mrp.Description, ansiFormatsModuleParametersParameterDescription) + '\n'
			parmDefinitionString = parmDefinitionString + '\n'
		if (len(modOptionalParms) > 0):
			parmDefinitionString = parmDefinitionString + '\n'
			parmDefinitionString = parmDefinitionString + liblogging.ANSITextFormat.ANSITextFormatString('- Optional Parameters -', ansiFormatsModuleParametersHeader) + '\n\n'
			for mrp in modOptionalParms:
				parmDefinitionString = parmDefinitionString + liblogging.ANSITextFormat.ANSITextFormatString(mrp.Name, ansiFormatsModuleParametersParameterName) + '\n'
				parmDefinitionString = parmDefinitionString + liblogging.ANSITextFormat.ANSITextFormatString(mrp.Description, ansiFormatsModuleParametersParameterDescription) + '\n'
				parmDefinitionString = parmDefinitionString + 'If this parameter is not explicitly specified, it will default to "' 
				mrpValue = '[Null]'
				if (mrp.CurrentValue):
					mrpValue = mrp.CurrentValue
				parmDefinitionString = parmDefinitionString + liblogging.ANSITextFormat.ANSITextFormatString(mrpValue, ansiFormatsOptions) + '"\n'
			parmDefinitionString = parmDefinitionString + '\n'
		
		liboutput.OutputUtils.PrettyPrintHelpFileSection(twidth, 'Parameters', parmDefinitionString, ansiFormatsModuleDetailsHeader, ansiFormatsModuleDetailsContent)

		dirListString = ''
		if (activeModule.SupportsDirectoryListings):
			dirListString = 'This module is marked as supporting directory listings (in other words, it should be capable of functioning correctly in --rooturi and --rooturilist modes in addition to -singleuri or --exacturilist).'
		else:
			dirListString = 'This module is marked as _not_ supporting directory listings (in other words, it will most likely function correctly only in --singleuri or --exacturilist modes). You will not be prevented from attempting to use the --rooturi and --rooturilist modes, but they are unlikely to work as expected.'
		liboutput.OutputUtils.PrettyPrintHelpFileSection(twidth, 'Directory Listings/Recursion', dirListString, ansiFormatsModuleDetailsHeader, ansiFormatsModuleDetailsContent)

		if (activeModule.RequiresSWAMM):
			swammString = 'This module requires the use of a She Wore A Mirrored Mask instance. Please see the On The Outside, Reaching In documentation for details.'
			liboutput.OutputUtils.PrettyPrintHelpFileSection(twidth, 'She Wore A Mirrored Mask', swammString, ansiFormatsModuleDetailsHeader, ansiFormatsModuleDetailsContent)

		liboutput.OutputUtils.PrettyPrintHelpFileSection(twidth, 'Required Parameter Details', activeModule.GetDataRequiredParameters(), ansiFormatsModuleDetailsHeader, ansiFormatsModuleDetailsContent, True)
		liboutput.OutputUtils.PrettyPrintHelpFileSection(twidth, 'Optional Parameter Details', activeModule.GetDataOptionalParameters(), ansiFormatsModuleDetailsHeader, ansiFormatsModuleDetailsContent)
		liboutput.OutputUtils.PrettyPrintHelpFileSection(twidth, 'Notes/Limitations', activeModule.GetDataNotesLimitations(), ansiFormatsModuleDetailsHeader, ansiFormatsModuleDetailsContent, True)
		liboutput.OutputUtils.PrettyPrintHelpFileSection(twidth, 'Examples', activeModule.GetDataExamples(), ansiFormatsModuleDetailsHeader, ansiFormatsModuleDetailsContent)
		liboutput.OutputUtils.PrettyPrintHelpFileSection(twidth, 'Tested Target Systems', activeModule.GetDataTestedTargets(), ansiFormatsModuleDetailsHeader, ansiFormatsModuleDetailsContent, True)
		liboutput.OutputUtils.PrettyPrintHelpFileSection(twidth, 'Authors', activeModule.GetDataAuthors(), ansiFormatsModuleDetailsHeader, ansiFormatsModuleDetailsContent, True)
		liboutput.OutputUtils.PrettyPrintHelpFileSection(twidth, 'Release Date', activeModule.GetDataReleaseDate(), ansiFormatsModuleDetailsHeader, ansiFormatsModuleDetailsContent, True)
		liboutput.OutputUtils.PrettyPrintHelpFileSection(twidth, 'Vulnerability Discovery and Disclosure', activeModule.GetDataVulnerabilityDisclosure(), ansiFormatsModuleDetailsHeader, ansiFormatsModuleDetailsContent, True)
		liboutput.OutputUtils.PrettyPrintHelpFileSection(twidth, 'Related Modules', activeModule.GetDataRelatedModules(), ansiFormatsModuleDetailsHeader, ansiFormatsModuleDetailsContent)
		liboutput.OutputUtils.PrettyPrintHelpFileSection(twidth, 'Comments', activeModule.GetDataComments(), ansiFormatsModuleDetailsHeader, ansiFormatsModuleDetailsContent)
		sys.exit(0)
	
	opmode = libotori.OtoriInstance.OPMODE_UNKNOWN
	
	if (opmode == libotori.OtoriInstance.OPMODE_UNKNOWN):
		if (args.clone):
			opmode = libotori.OtoriInstance.OPMODE_CLONE

	if (opmode == libotori.OtoriInstance.OPMODE_UNKNOWN):
		if (args.test):
			opmode = libotori.OtoriInstance.OPMODE_TEST
			multiLogger.critical('Test functionality is not currently implemented.')
			sys.exit(1)

	if (opmode == libotori.OtoriInstance.OPMODE_UNKNOWN):
		if (args.doslulz):
			opmode = libotori.OtoriInstance.OPMODE_DOSLULZ

	if (opmode == libotori.OtoriInstance.OPMODE_UNKNOWN):
		if (args.dosquad):
			opmode = libotori.OtoriInstance.OPMODE_DOSQUAD
			
	if (opmode == libotori.OtoriInstance.OPMODE_UNKNOWN):
		if (args.portscan):
			opmode = libotori.OtoriInstance.OPMODE_PORTSCAN
			multiLogger.critical('Port-scanning functionality is not currently implemented.')
			sys.exit(1)

	if (opmode == libotori.OtoriInstance.OPMODE_UNKNOWN):
		if (args.xxeproxy):
			opmode = libotori.OtoriInstance.OPMODE_XXEPROXY
			multiLogger.critical('Proxying via XXE is not currently implemented.')
			sys.exit(1)

	if (opmode == libotori.OtoriInstance.OPMODE_UNKNOWN):
		parser.print_help()
		multiLogger.critical('No valid operating mode was specified!')
		sys.exit(1)
	
	
	requestRootOrList = ''
	requestMode = libotori.OtoriInstance.REQUESTMODE_UNKNOWN
	if ((opmode == libotori.OtoriInstance.OPMODE_CLONE)):
		if (args.singleuri):
			requestRootOrList = args.singleuri
			requestMode = libotori.OtoriInstance.REQUESTMODE_SINGLEURI
		if (args.rooturi):
			requestRootOrList = args.rooturi
			requestMode = libotori.OtoriInstance.REQUESTMODE_ROOTURI
		if (args.exacturilist):
			requestRootOrList = args.exacturilist
			requestMode = libotori.OtoriInstance.REQUESTMODE_EXACTURILIST
		if (args.rooturilist):
			requestRootOrList = args.rooturilist
			requestMode = libotori.OtoriInstance.REQUESTMODE_ROOTURILIST
		
		if (requestRootOrList == ''):
			multiLogger.critical('No valid URI (or list of URIs) was specified!')
			sys.exit(1)
			
	
	existingfilesmode = libotori.OtoriInstance.EXISTINGFILES_UNKNOWN

	if ((opmode == libotori.OtoriInstance.OPMODE_CLONE)):
		if (existingfilesmode == libotori.OtoriInstance.EXISTINGFILES_UNKNOWN):
			if (args.preserve):
				existingfilesmode = libotori.OtoriInstance.EXISTINGFILES_PRESERVE
		
		if (existingfilesmode == libotori.OtoriInstance.EXISTINGFILES_UNKNOWN):
			if (args.overwrite):
				existingfilesmode = libotori.OtoriInstance.EXISTINGFILES_OVERWRITE
				
		if (existingfilesmode == libotori.OtoriInstance.EXISTINGFILES_UNKNOWN):
			if (args.version):
				existingfilesmode = libotori.OtoriInstance.EXISTINGFILES_VERSION
		
		if (existingfilesmode == libotori.OtoriInstance.EXISTINGFILES_UNKNOWN):
			parser.print_help()
			multiLogger.critical('You must specify one of --preserve, --overwrite, or --version!')
			sys.exit(1)
	
	foundOptions = False
	
	if (args.moduleoptions):
		if (len(args.moduleoptions) > 0):
			#targetURLs = args.moduleoptions[0]
			multiLogger.debug('Setting module options from array with {0} element(s)'.format(len(args.moduleoptions[0])))
			optionNumber = 1
			for option in args.moduleoptions[0]:
				multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Option {0}: '.format(optionNumber), option, ansiFormatsOutputHeaders, ansiFormatsOptions))
				optionNumber = optionNumber + 1
			try:
				activeModule.SetOptionsFromCommandLineArgs(args.moduleoptions[0])
			except Exception as e:
				multiLogger.critical('Not enough parameters were supplied for the specified module, or they were specified in an incorrect format')
				sys.exit(1)
			foundOptions = True
	
	if not (foundOptions):
		multiLogger.critical('All modules require at least one option to be specified - some require several - see the documentation for the module you are using')
		sys.exit(1)	
		
	outputBaseAbsolutePath = libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/output/')
	
	if (args.outputbase):
		outputBaseAbsolutePath = os.path.abspath(args.outputbase)
		
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Operating mode: ', libotori.OtoriInstance.GetOperationModeName(opmode), ansiFormatsOutputHeaders, ansiFormatsOptions))
	
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Output will be generated in: ', outputBaseAbsolutePath, ansiFormatsOutputHeaders, ansiFormatsOptions))
	
	if (isinstance(activeModule, libxxeexploits.XXEHTTP)):
		multiLogger.debug('Setting HTTP/HTTPS-specific module options')
		if (args.httpUserAgent):
			activeModule.FixedUserAgent = args.httpUserAgent
		if (args.httpCookie):
			activeModule.CookieString = args.httpCookie

	# this is a separate variable so that SWAMM can be optionally used for things like content-obfuscation in the future
	swammRequired = False
	if (activeModule.RequiresSWAMM):
		swammRequired = True
		
	swammURLs = libswamm.SWAMMURLSet()
	if (args.swammURLBase):
		swammURLs.BaseURL = args.swammURLBase
	if (args.swammURLRead):
		swammURLs.ReadURL = args.swammURLRead
	if (args.swammURLWrite):
		swammURLs.WriteURL = args.swammURLWrite
	if (args.swammURLAppend):
		swammURLs.AppendURL = args.swammURLAppend
	if (args.swammURLDelete):
		swammURLs.DeleteURL = args.swammURLDelete
	if (args.swammURLStoreAdd):
		swammURLs.StoreAddURL = args.swammURLStoreAdd
	if (args.swammURLStoreDelete):
		swammURLs.StoreDeleteURL = args.swammURLStoreDelete
		
	if (swammRequired):
		missingSWAMMParams = False
		if not (swammURLs.BaseURL):
			multiLogger.critical('The current operating configuration requires the use of a She Wore A Mirrored Mask instance, but no base URL was specified')
			missingSWAMMParams = True
		if not (swammURLs.ReadURL):
			multiLogger.critical('The current operating configuration requires the use of a She Wore A Mirrored Mask instance, but no read URL was specified')
			missingSWAMMParams = True
		if not (swammURLs.WriteURL):
			multiLogger.critical('The current operating configuration requires the use of a She Wore A Mirrored Mask instance, but no write URL was specified')
			missingSWAMMParams = True
		if not (swammURLs.AppendURL):
			multiLogger.critical('The current operating configuration requires the use of a She Wore A Mirrored Mask instance, but no append URL was specified')
			missingSWAMMParams = True
		if not (swammURLs.DeleteURL):
			multiLogger.critical('The current operating configuration requires the use of a She Wore A Mirrored Mask instance, but no delete URL was specified')
			missingSWAMMParams = True
		if not (swammURLs.StoreAddURL):
			multiLogger.critical('The current operating configuration requires the use of a She Wore A Mirrored Mask instance, but no stored request/response add URL was specified')
			missingSWAMMParams = True
		if not (swammURLs.StoreDeleteURL):
			multiLogger.critical('The current operating configuration requires the use of a She Wore A Mirrored Mask instance, but no stored request/response delete URL was specified')
			missingSWAMMParams = True
		if (missingSWAMMParams):
			multiLogger.critical('Please re-run On The Outside, Reaching In with all of the required She Wore A Mirrored Mask URLs, or use a configuration that does not require She Wore A Mirrored Mask')
			sys.exit(1)
		multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('She Wore A Mirrored Mask base URL: ', swammURLs.BaseURL, ansiFormatsOutputHeaders, ansiFormatsOptions))
		multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('She Wore A Mirrored Mask read URL: ', swammURLs.ReadURL, ansiFormatsOutputHeaders, ansiFormatsOptions))
		multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('She Wore A Mirrored Mask write URL: ', swammURLs.WriteURL, ansiFormatsOutputHeaders, ansiFormatsOptions))
		multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('She Wore A Mirrored Mask append URL: ', swammURLs.AppendURL, ansiFormatsOutputHeaders, ansiFormatsOptions))
		multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('She Wore A Mirrored Mask delete URL: ', swammURLs.DeleteURL, ansiFormatsOutputHeaders, ansiFormatsOptions))
		multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('She Wore A Mirrored Mask stored request/response add URL: ', swammURLs.StoreAddURL, ansiFormatsOutputHeaders, ansiFormatsOptions))
		multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('She Wore A Mirrored Mask stored request/response delete URL: ', swammURLs.StoreDeleteURL, ansiFormatsOutputHeaders, ansiFormatsOptions))

	activeModule.SWAMMURLs = swammURLs
		
	memoryUse = 0
	memoryExpansionString = ''
	if (opmode == libotori.OtoriInstance.OPMODE_CLONE):
		discardErrorFiles = False
		if (args.noerrorfiles):
			discardErrorFiles = True
		GenerateOptionOutputForRetainDiscard(multiLogger, 'Results which generate an error will be: ', discardErrorFiles, ansiFormatsOutputHeaders, ansiFormatsOptions)

		discardEmptyFiles = False
		if (args.noemptyfiles):
			discardEmptyFiles = True
		GenerateOptionOutputForRetainDiscard(multiLogger, 'Files which are empty will be: ', discardEmptyFiles, ansiFormatsOutputHeaders, ansiFormatsOptions)

		discardWhitespaceFiles = False
		if (args.nowhitespacefiles):
			discardWhitespaceFiles = True
		GenerateOptionOutputForRetainDiscard(multiLogger, 'Files which contain only whitespace will be: ', discardWhitespaceFiles, ansiFormatsOutputHeaders, ansiFormatsOptions)
		
		discardEmptyDirs = False
		if (args.noemptydirs):
			discardEmptyDirs = True
		GenerateOptionOutputForRetainDiscard(multiLogger, 'Directories which are empty will be: ', discardEmptyDirs, ansiFormatsOutputHeaders, ansiFormatsOptions)
		
		inst = libotori.OtoriInstanceClone(multiLogger, activeModule, requestMode, requestRootOrList, outputBaseAbsolutePath, existingfilesmode, args.requesttimeout, args.retries, args.requestwaittime, args.requestwaittimewindow, args.maxdepth, discardErrorFiles, discardEmptyFiles, discardWhitespaceFiles, discardEmptyDirs)
		
		#if ((requestMode == libotori.OtoriInstance.REQUESTMODE_ROOTURI) or (requestMode == libotori.OtoriInstance.REQUESTMODE_ROOTURILIST)):
			#directoryTestText = 'semi-intelligent'
			#if (args.tarad):
				#inst.UseIntelligentFileVersusDirectoryLogic = False
				#directoryTestText = 'semi-brute-force'
			#multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('File-versus-directory determination: ', directoryTestText, ansiFormatsOutputHeaders, ansiFormatsOptions))
		
	if (opmode == libotori.OtoriInstance.OPMODE_TEST):
		print 'Do some stuff'
	if (opmode == libotori.OtoriInstance.OPMODE_PORTSCAN):
		print 'Do some stuff'
	if (opmode == libotori.OtoriInstance.OPMODE_XXEPROXY):
		print 'Do some stuff'
	if (opmode == libotori.OtoriInstance.OPMODE_DOSLULZ):
		inst = libotori.OtoriInstanceDoSLulz(multiLogger, activeModule, outputBaseAbsolutePath, args.requesttimeout, args.retries, args.requestwaittime, args.requestwaittimewindow, args.dosstring, args.doslulzbase, args.doslulzexp)
		memoryExpansionString = str(args.doslulzbase) + '^' + str(args.doslulzexp)
		memoryUse = len(args.dosstring) * (math.pow(args.doslulzbase, args.doslulzexp))
	if (opmode == libotori.OtoriInstance.OPMODE_DOSQUAD):
		inst = libotori.OtoriInstanceDoSQuad(multiLogger, activeModule, outputBaseAbsolutePath, args.requesttimeout, args.retries, args.requestwaittime, args.requestwaittimewindow, args.dosstring, args.dosquadbase, args.dosquadmult)	
		memoryUse = len(args.dosstring) * (args.dosquadbase * args.dosquadmult)
		memoryExpansionString = str(args.dosquadbase) + ' * ' + str(args.dosquadmult)
		

	if (opmode == libotori.OtoriInstance.OPMODE_DOSLULZ) or (opmode == libotori.OtoriInstance.OPMODE_DOSQUAD):
		memoryUseString = liboutput.OutputUtils.GetByteCountStringInSIUnits(memoryUse) + ' / ' + liboutput.OutputUtils.GetByteCountStringInBinaryUnits(memoryUse)
		multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Denial-of-service string: ', args.dosstring, ansiFormatsOutputHeaders, ansiFormatsOptions))
		multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Target string expansion: ', memoryExpansionString, ansiFormatsOutputHeaders, ansiFormatsOptions))
		multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Target minimum memory use: ', memoryUseString, ansiFormatsOutputHeaders, ansiFormatsOptions))
		
		
	activeModule.SetParentOtoriInstance(inst)
	
	if (args.uriblacklist):
		inst.loadURIBlacklist(args.uriblacklist)

	mainThreadAborted = False
	try:
		results = inst.Operate()
	except KeyboardInterrupt:
		multiLogger.warning('Aborting due to user-initiated keyboard sequence')
		mainThreadAborted = True
		sys.exit(7)

	gotResults = False
	if (results):
		try:
			if (len(results) > 0):
				gotResults = True
		except:
			gotResults = False

	if ((opmode == libotori.OtoriInstance.OPMODE_CLONE)):
		if (args.reportfile):
			if (args.reportfile.strip() != ''):
				if (gotResults):
					multiLogger.info('Writing tab-delimited report file "' + args.reportfile + '"')
					resultReport = ''
					resultReport = resultReport + 'Remote URI\tLocal Path\tDownloaded\tResult\tSize\n'
					for r in results:
						resultUri = 'Unknown'
						resultLocalPath = 'Unknown'
						downloaded = 'True'
						resultType = 'Unknown'
						localSize = 'N/A'
						defaultValue = 'Null Result'
						try:
							resultUri = libotori.OtoriInstance.getPathForHumanReadableOutput(r.XXETarget)
						except:
							resultUri = defaultValue
							multiLogger.error('Unable to obtain the URI from a result object')
						try:
							resultLocalPath = libotori.OtoriInstance.getPathForHumanReadableOutput(r.LocalPath)
						except:
							resultLocalPath = defaultValue
							multiLogger.error('Unable to obtain the local path from a result object')
						try:
							if (r.returnCode > 0):
								downloaded = 'False'
						except:
							downloaded = defaultValue
							multiLogger.error('Unable to obtain the return code from a result object')
						#try:
						resultType = libxxeexploits.XXEResponse.GetReturnCodeTypeName(r.ReturnCode)
						#except:
						#	resultType = defaultValue
						#	multiLogger.error('Unable to obtain the return code type name from a result object')
						try:
							if (r.LocalSize):
								localSize = str(r.LocalSize)
						except:
							localSize = defaultValue
							multiLogger.error('Unable to obtain the local file size from a result object')
							
						resultReport = resultReport + resultUri + '\t' + resultLocalPath + '\t' + downloaded + '\t' + resultType + '\t' + localSize + '\n'
					try:
						libfileio.FileWriter.WriteFile(args.reportfile, resultReport)
					except libfileio.FileWriteError as e:
						multiLogger.error(e.msg)
					except:
						multiLogger.error('Unable to write report file "' + args.reportfile + '": ' + str(sys.exc_info()[0]))
				else:
					multiLogger.warning('The command-line option to generate a tab-delimited report file (to "' + args.reportfile + '") was specified, but no results were generated to be written to that file, so it will not be created')

	endTimestampUTC = datetime.datetime.utcnow()
	endTimestamp = datetime.datetime.now()
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Execution began: ', liboutput.OutputUtils.GetFormattedDateTime(startTimestamp), ansiFormatsOutputHeaders, ansiFormatsOutputDetails))
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Execution completed: ', liboutput.OutputUtils.GetFormattedDateTime(endTimestamp), ansiFormatsOutputHeaders, ansiFormatsOutputDetails))
	#multiLogger.info('Execution began: {0}'.format(liboutput.OutputUtils.GetFormattedDateTime(startTimestamp)))
	#multiLogger.info('Execution completed: {0}'.format(liboutput.OutputUtils.GetFormattedDateTime(endTimestamp)))

	timeDiff = endTimestampUTC - startTimestampUTC
	totalSeconds = timeDiff.total_seconds()
	if (totalSeconds > 0):
		multiLogger.info('Total time elapsed: {0}'.format(liboutput.OutputUtils.GetFormattedDateTimeDifference(timeDiff)))
	else:
		multiLogger.warning('Your clock appears to be experiencing synchronization problems - the total time elapsed has been calculated as {0} seconds - if you have the ability to travel backwards in time and have intentionally made use of that ability, you can safely ignore this warning'.format(totalSeconds))

	if (gotResults):
		resultCounts = {}
		for r in results:
			resultType = 'Unknown'
			resultType = libxxeexploits.XXEResponse.GetReturnCodeTypeName(r.ReturnCode)
			if (resultType in resultCounts.keys()):
				resultCounts[resultType] = resultCounts[resultType] + 1
			else:
				resultCounts[resultType] = 1
		if (len(resultCounts) > 0):
			resultTypes = resultCounts.keys()
			resultTypes.sort()
			multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Clone operation result statistics:', '', ansiFormatsOutputHeaders, ansiFormatsOutputDetails))
			for rt in resultTypes:
				multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('     {0}: '.format(rt), str(resultCounts[rt]), ansiFormatsOutputHeaders, ansiFormatsOutputDetails))
		else:
			if (opmode == libotori.OtoriInstance.OPMODE_CLONE):
				multiLogger.warning('No files were downloaded')
	
if __name__ == "__main__":
    main()