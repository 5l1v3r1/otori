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
import datetime
import httplib
import logging
import math
import os
import re
import subprocess
import sys

import libdeceitfulhttp
import libdeceitfulnetwork
import libfileio
import liblogging
import libotori
import liboutput
import libswamm
import libswammserverprofiles
import libxxeexploits
import xxeexploitmodules

__author__ = 'Ben Lincoln - http://www.beneaththewaves.net/'






def GetVersion():
	return '0.3 - 2014-07-20'

def GetProgramName():
	return 'She Wore A Mirrored Mask ("SWAMM") version {0}'.format(GetVersion())

def GetLogoFile(subdirectory):
	fullPath = libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/data/swamm/banners/{0}'.format(subdirectory))
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
	titleTextFormatting = ['BG_BLACK', 'FG_BLUE', 'BOLD']
	titleSubTextFormatting = ['BG_BLACK', 'FG_CYAN', 'FAINT']
	titleCreedFormatting = ['BG_BLACK', 'FG_WHITE', 'FAINT']
	if not (useANSIFormatting):
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
	programDescription = 'A webserver with hidden talents'
	result = result + liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.CenterStringWithPaddingChars(terminalWidth, ' ', programDescription, ' '), titleSubTextFormatting)
	result = result + '\n'
	programCreed = '==[ For use only in ways which are both lawful and ethical ]=='
	result = result + liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.CenterStringWithPaddingChars(terminalWidth, ' ', programCreed, ' '), titleCreedFormatting)
	result = result + liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.CenterStringWithPaddingChars(terminalWidth, ' ', '  ', ' '), titleCreedFormatting)
	result = result + '\n\n'
	result = result + liboutput.OutputUtils.CenterString(terminalWidth, 'Copyright 2014 Ben Lincoln')
	result = result + '\n'
	result = result + liboutput.OutputUtils.CenterString(terminalWidth, 'http://www.beneaththewaves.net/Software/She_Wore_A_Mirrored_Mask.html')
	result = result + '\n'
	result = result + liboutput.OutputUtils.CenterString(terminalWidth, 'Visit http://www.beneaththewaves.net/Software/ for detailed tutorials')
	result = result + '\n'
	result = result + liboutput.OutputUtils.CenterString(terminalWidth, 'Released under version 3 of the GPL - see the accompanying LICENSE.txt file')
	result = result + '\n\n'
	return result

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
	parser.add_argument("--address", dest='listenAddress', metavar='IP_ADDRESS', help="the address to listen on for connections (default: 0.0.0.0 - all interfaces)", default='0.0.0.0')
	parser.add_argument("--port", type=int, dest='listenPort', metavar='TCP_PORT', help="the port to listen on for connections (default: 8080)", default=8080)
	parser.add_argument("--ssl-server-cert", dest='sslCertPath', metavar='FILE_PATH', help="the path to the file containing a fixed SSL server public certificate to present to clients")
	parser.add_argument("--ssl-server-key", dest='sslKeyPath', metavar='FILE_PATH', help="the path to the file containing a fixed SSL server private key to use when communicating with clients")	
	
	parser.add_argument("--uri-prefix-master", dest='uriPrefixMaster', metavar='URI_PREFIX', help="the URI stem prefix to which other special URI stems will be appended if they are not explicitly specified (will be randomly generated if it is not explicitly specified)", default=None)
	parser.add_argument("--uri-prefix-read", dest='uriPrefixRead', metavar='URI_PREFIX', help="the URI stem prefix to use for read operations (will be randomly generated based on the master URI stem prefix if it is not explicitly specified)", default=None)
	parser.add_argument("--uri-prefix-write", dest='uriPrefixWrite', metavar='URI_PREFIX', help="the URI stem prefix to use for write operations (will be randomly generated based on the master URI stem prefix if it is not explicitly specified)", default=None)
	parser.add_argument("--uri-prefix-append", dest='uriPrefixAppend', metavar='URI_PREFIX', help="the URI stem prefix to use for append operations (will be randomly generated based on the master URI stem prefix if it is not explicitly specified)", default=None)
	parser.add_argument("--uri-prefix-delete", dest='uriPrefixDelete', metavar='URI_PREFIX', help="the URI stem prefix to use for delete operations (will be randomly generated based on the master URI stem prefix if it is not explicitly specified)", default=None)
	parser.add_argument("--uri-prefix-store-add", dest='uriPrefixStoreAdd', metavar='URI_PREFIX', help="the URI stem prefix to use for storing request/response pairs (will be randomly generated based on the master URI stem prefix if it is not explicitly specified)", default=None)
	parser.add_argument("--uri-prefix-store-delete", dest='uriPrefixStoreDelete', metavar='URI_PREFIX', help="the URI stem prefix to use for deleting request/response pairs (will be randomly generated based on the master URI stem prefix if it is not explicitly specified)", default=None)
	
	#parser.add_argument("--rules-forward-network", dest='rulesForwardNetwork', metavar='RULE', default=[], help="one or more network-level port-forwarding rules - see the documentation for details", action='append', nargs='+')
	parser.add_argument("--rules-forward-network", dest='rulesForwardNetwork', metavar='RULE', default=[], help="this option is not currently implemented or supported", action='append', nargs='+')
	
	parser.add_argument("--masq-list", dest='masqueradeList', help="list available pre-defined webserver-masquerading modes", action="store_true")	
	parser.add_argument("--masq-predefined", dest='masqueradePredefined', metavar='MASQUERADE_MODE_NAME', help="use one of the predefined webserver-masquerading modes - if this option is not explicitly specified, the Apache Coyote 1.1 profile will be used by default")
	parser.add_argument("--masq-serverstring", dest='masqueradeServerString', metavar='MASQUERADE_SERVER_STRING', help="return the specified string as the Server HTTP header to clients (will override the string in the predefined masquerade mode, while still using the response bodies from the predefined mode that is in use)")	

	parser.add_argument("--console-verbosity", dest='consoleVerbosity', choices=['debug', 'info', 'warning', 'error', 'critical'], help="set the level of verbosity for console output", default='info')
	parser.add_argument("--log-verbosity", dest='logfileVerbosity', choices=['debug', 'info', 'warning', 'error', 'critical'], help="set the level of verbosity for log file output (only used if --log is specified)", default='info')
	parser.add_argument("--log", dest='logfilePath', metavar='LOG_FILE_PATH', help="specify an optional file to which console-type messages should be logged - will be appended to if it already exists")
	#parser.add_argument("--log-w3c", dest='w3cLogfilePath', metavar='W3C_LOG_FILE_PATH', help="specify an optional file to which W3C-style webserver log entries will be written - will be appended to if it already exists")	
	parser.add_argument("--log-w3c", dest='w3cLogfilePath', metavar='W3C_LOG_FILE_PATH', help="this option is not currently implemented or supported")	
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
	multiLogger.info('Operation beginning: {0}'.format(liboutput.OutputUtils.GetFormattedDateTime(startTimestamp)))
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Console verbosity: ', consoleLogLevel.Name, ansiFormatsOutputHeaders, ansiFormatsOptions))
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Log file verbosity: ', logfileLogLevel.Name, ansiFormatsOutputHeaders, ansiFormatsOptions))
	if (usingLogFile):
		multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Log file: ', args.logfilePath, ansiFormatsOutputHeaders, ansiFormatsOptions))
			
	if (args.usage):
		parser.print_help()
		print libfileio.FileReader.getFileAsString(libfileio.FileReader.getAbsoluteFilePathFromModuleBase('/data/helptext.txt'))
		sys.exit(0)

	if (args.noansi):
		multiLogger.warning('ANSI text formatting has been disabled. 31 out of 33 "l33+" "hax0rs" leave ANSI text formatting enabled, but not everyone has what it takes to "[get] r3wt on all j00r b0xx0rz".')

	serverProfileList = libswammserverprofiles.HTTPServerResponseProfileEnumerator()
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Server profiles available: ', str(len(serverProfileList.Profiles)), ansiFormatsOutputHeaders, ansiFormatsOutputDetails))
		
	if (args.masqueradeList):
		print liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.CenterStringWithPaddingChars(twidth, ' ', '- Available Server Profiles -', ' '), ansiFormatsOutputHeaders)
		
		col1Width = 24
		col2Width = twidth - col1Width
		columnWidths = [col1Width, col2Width]
		
		headerStrings = ['Profile ID', 'Name']
		
		headerBlock = liblogging.ANSITextFormat.ANSITextFormatString(liboutput.OutputUtils.FormatTextAsTable(headerStrings, columnWidths, centerText = True), ansiFormatsModuleListHeaders)
		print headerBlock
			
		for p in serverProfileList.Profiles:
			modStrings = []

			modStrings.append(liblogging.ANSITextFormat.ANSITextFormatString(p.UID, ansiFormatsModuleListUID))
			modStrings.append(liblogging.ANSITextFormat.ANSITextFormatString(p.Name, ansiFormatsModuleListDescription))
			modBlock = liboutput.OutputUtils.FormatTextAsTable(modStrings, columnWidths)
			print modBlock
			print ''
		sys.exit(0)
	
	serverProfile = None
	serverProfileString = None
	
	if (args.masqueradePredefined):
		serverProfile = serverProfileList.GetProfileByUID(args.masqueradePredefined)
		if not (serverProfile):
			multiLogger.critical('Could not find a server profile with ID "' + args.masqueradePredefined + '"')
			sys.exit(1)
	else:
		serverProfile = serverProfileList.Profiles[0]
	
	
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Using HTTP server profile: ', serverProfile.UID, ansiFormatsOutputHeaders, ansiFormatsOptions))
	
	if (args.masqueradeServerString):
		serverProfile.ResponseVariables['%SERVERNAME%'] = args.masqueradeServerString

	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Using HTTP server header value: ', serverProfile.ResponseVariables['%SERVERNAME%'], ansiFormatsOutputHeaders, ansiFormatsOptions))
		
		
	listeningAddress = libdeceitfulnetwork.Layer3Address()
	#listeningAddress.IPAddress = '0.0.0.0'
	#listeningAddress.Port = 8998
	listeningAddress.IPAddress = args.listenAddress
	listeningAddress.Port = args.listenPort
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Will listen on IP address: ', listeningAddress.IPAddress, ansiFormatsOutputHeaders, ansiFormatsOptions))
	multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('Will listen on TCP port: ', str(listeningAddress.Port), ansiFormatsOutputHeaders, ansiFormatsOptions))
		
	sslCertPath = None
	sslKeyPath = None
	if (args.sslCertPath):
		if (os.path.exists(args.sslCertPath)):
			sslCertPath = args.sslCertPath
		else:
			multiLogger.error('Could not find a file with the path "{0}", which was specified for the SSL/TLS certificate - SSL/TLS will be disabled')
	if (args.sslKeyPath):
		if (os.path.exists(args.sslKeyPath)):
			sslKeyPath = args.sslKeyPath
		else:
			multiLogger.error('Could not find a file with the path "{0}", which was specified for the SSL/TLS private key - SSL/TLS will be disabled')

	if (sslCertPath):
		if not (sslKeyPath):
			multiLogger.error('An SSL/TLS certificate file was specified, but no key file was specified - SSL/TLS will be disabled')
			sslCertPath = None
	else:
		if (sslKeyPath):
			multiLogger.error('An SSL/TLS key file was specified, but no certificate file was specified - SSL/TLS will be disabled')
			sslKeyPath = None
			
	if ((sslCertPath) and (sslKeyPath)):
		multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('SSL/TLS certificate file: ', sslCertPath, ansiFormatsOutputHeaders, ansiFormatsOptions))
		multiLogger.info(liboutput.OutputUtils.GenerateOptionOutput('SSL/TLS key file: ', sslKeyPath, ansiFormatsOutputHeaders, ansiFormatsOptions))
		
	
	#svr = libdeceitfulhttp.DeceitfulHTTPServer(multiLogger)
	
	svr = libswamm.SWAMMServer(multiLogger, args.uriPrefixMaster, args.uriPrefixRead, args.uriPrefixWrite, args.uriPrefixAppend, args.uriPrefixDelete, args.uriPrefixStoreAdd, args.uriPrefixStoreDelete)

	if (serverProfile):
		svr.ServerProfile = serverProfile
		
	#if (serverProfileString):
		#svr.ServerProfile.ResponseVariables['%SERVERNAME%'] = serverProfileString
	
	svr.ListeningLayer3Addresses.append(listeningAddress)

	if ((sslCertPath) and (sslKeyPath)):
		svr.SSLCertFile = sslCertPath
		svr.SSLKeyFile = sslKeyPath
		
	mainThreadAborted = False
	try:
		#print 'To do: make this program do anything useful. OLOL.'

		svr.Run()
	except KeyboardInterrupt:
		multiLogger.warning('- Interrupt -')
		multiLogger.warning('Aborting due to user-initiated keyboard sequence')
		multiLogger.warning('Please wait for existing connections to close, or press Ctrl-C again to immediately exit (this may cause server ports to remain in use until the OS-level networking subsystem times them out)')
		svr.Stop()
		mainThreadAborted = True
	try:
		svr.WaitForShutdown()
	except KeyboardInterrupt:
		multiLogger.warning('- Interrupt -')
		multiLogger.warning('Exiting immediately (this may cause server ports to remain in use until the OS-level networking subsystem times them out)')
		shutdownThreadAborted = True
		sys.exit(7)
	
	endTimestampUTC = datetime.datetime.utcnow()
	endTimestamp = datetime.datetime.now()
	multiLogger.info('Operation began: {0}'.format(liboutput.OutputUtils.GetFormattedDateTime(startTimestamp)))
	multiLogger.info('Operation terminated: {0}'.format(liboutput.OutputUtils.GetFormattedDateTime(endTimestamp)))

	timeDiff = endTimestampUTC - startTimestampUTC
	totalSeconds = timeDiff.total_seconds()
	if (totalSeconds > 0):
		multiLogger.info('Total operation time: {0}'.format(liboutput.OutputUtils.GetFormattedDateTimeDifference(timeDiff)))
	else:
		multiLogger.warning('Your clock appears to be experiencing synchronization problems - the total time elapsed has been calculated as {0} seconds - if you have the ability to travel backwards in time and have intentionally made use of that ability, you can safely ignore this warning'.format(totalSeconds))

if __name__ == "__main__":
    main()	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	