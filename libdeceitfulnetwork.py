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

import socket
import thread

class NetworkLevelResponse():
	def __init__(self):
		self.Error = False
		self.ResponseCode = 0
		self.Message = ''
		
	def SetValuesFromExceptionArgs(self, exceptionArgs):
		if (len(exceptionArgs) > 0):
			self.ResponseCode = exceptionArgs[0]
			try:
				# I think this is right, but not actually sure
				if (int(self.ResponseCode) > 0):
					self.Error = True
			except:
				self.Error = True
		if (len(exceptionArgs) > 1):
			self.Message = exceptionArgs[1]

# This is not a robust name-lookup system - it will cache entries indefinitely, for example
class CachedLayer3AddressList():
	def __init__(self):
		self.Cache = {}

	def DoThreadedLookup(self, newEntry, multiLogger = None):
		newEntry.SetNamesUsingLookup(multiLogger)
		self.Cache[newEntry.IPAddress] = newEntry
		
	def GetEntryByAddress(self, address, multiLogger = None):
		for entryKey in self.Cache.keys():
			entry = self.Cache[entryKey]
			if (entry.IPAddress == address):
				return entry
		newEntry = Layer3Address()
		newEntry.IPAddress = address
		newEntry.SetNamesWithoutLookup(multiLogger)
		# for no delay even on first request!
		self.Cache[newEntry.IPAddress] = newEntry
		thread.start_new_thread(self.DoThreadedLookup, (newEntry, multiLogger))
		#newEntry.SetNamesUsingLookup(multiLogger)
		#self.Cache[newEntry.IPAddress] = newEntry
		return newEntry
			
class Layer3Address():
	def __init__(self):
		self.IPAddress = ''
		self.AlternateIPs = []
		self.HostName = None
		self.HostAliases = []
		self.HostFQDN = None
		self.Port = 0

	def SetNamesWithoutLookup(self, multiLogger = None):
		if (self.IPAddress == '0.0.0.0'):
			self.HostName = "all_local_interfaces"
		if (self.IPAddress == '127.0.0.1'):
			self.HostName = "loopback"

	def SetNamesUsingLookup(self, multiLogger = None):
		newHostName = None
		newAliasList = []
		newAlternateIPs = []
		
		self.SetNamesWithoutLookup(multiLogger)
		
		#if (self.IPAddress == '0.0.0.0'):
			##if not (self.HostName):
			##	self.HostName = "all_local_interfaces"
			#self.HostName = "all_local_interfaces"
		#else:
		try:
			newHostName, newAliasList, newAlternateIPs = socket.gethostbyaddr(self.IPAddress)
		except Exception as e:
			if (multiLogger):
				multiLogger.debug('Could not obtain the host name for IP address "{0}" from the socket library - {1} - {2}'.format(self.IPAddress, str(type(e)), str(e.args)))
			newHostName = None
		if (newHostName == None):
			if (multiLogger):
				multiLogger.debug('Host name for IP address "{0}" is unchanged ("{1}")'.format(self.IPAddress, str(self.HostName)))
		else:
			self.HostName = newHostName
			if (multiLogger):
				multiLogger.debug('Set host name for IP address "{0}" to "{1}"'.format(self.IPAddress, str(self.HostName)))

		gotNewAliasList = True
		if not (newAliasList):
			gotNewAliasList = False
		else:
			if (len(newAliasList) == 0):
				gotNewAliasList = False
		if (gotNewAliasList):
			self.HostAliases = newAliasList
			if (multiLogger):
				multiLogger.debug('Set alias list for IP address "{0}" to "{1}"'.format(self.IPAddress, str(self.HostAliases)))
		else:
			if (multiLogger):
				multiLogger.debug('Alias list for IP address "{0}" is unchanged ("{1}")'.format(self.IPAddress, str(self.HostAliases)))

		gotNewAlternateIPs = True
		if not (newAlternateIPs):
			gotNewAlternateIPs = False
		else:
			if (len(newAlternateIPs) == 0):
				gotNewAlternateIPs = False
		if (gotNewAlternateIPs):
			self.AlternateIPs = newAlternateIPs
			if (multiLogger):
				multiLogger.debug('Set alternate IP list for IP address "{0}" to "{1}"'.format(self.IPAddress, str(self.AlternateIPs)))
		else:
			if (multiLogger):
				multiLogger.debug('Alternate IP list for IP address "{0}" is unchanged ("{1}")'.format(self.IPAddress, str(self.AlternateIPs)))

		
		newFQDN = None
		if (self.HostName):
			try:
				newFQDN = socket.getfqdn()
			except Exception as e:
				if (multiLogger):
					multiLogger.debug('Could not obtain the host FQDN from the socket library for host name "{0}" - {1} - {2}'.format(self.HostName, str(type(e)), str(e.args)))
				newFQDN = None
			if (newFQDN):
				self.HostFQDN = newFQDN
				if (multiLogger):
					multiLogger.debug('Set FQDN for host "{0}" to "{1}"'.format(str(self.HostName), str(self.HostFQDN)))
		else:
			if (multiLogger):
				multiLogger.debug('No name is currently set for IP address "{0}", so the FQDN will not be set'.format(self.IPAddress))
	
	def GetFormattedName(self, useFQDNIfAvailable = False):
		result = ''
		hostName = self.HostName
		if ((useFQDNIfAvailable) and (self.HostFQDN)):
			hostName = self.HostFQDN
		
		if (self.IPAddress == ''):
			if (hostName):
				result = '[{0}:{1}]'.format(str(hostName), str(self.Port))
			else:
				result = '[unknown:{1}]'.format(str(self.Port))
		else:
			if (hostName):
				result = '[{0}:{1} ({2}:{3})]'.format(str(hostName), str(self.Port), str(self.IPAddress), str(self.Port))
			else:
				result = '[{0}:{1}]'.format(str(self.IPAddress), str(self.Port))
		return result		

	def ValuesMatch(self, comparisonObject, includeAlternateIPs = False, includeHostAliases = False, includePort = False, multiLogger = None):
		if (self.IPAddress != comparisonObject.IPAddress):
			if (multiLogger):
				multiLogger.debug('IP addresses do not match ("{0}", "{1}")'.format(self.IPAddress, comparisonObject.IPAddress))
			return False
		if (includeAlternateIPs):
			if (self.AlternateIPs != comparisonObject.AlternateIPs):
				if (multiLogger):
					multiLogger.debug('Alternate IPs do not match ("{0}", "{1}")'.format(self.AlternateIPs, comparisonObject.AlternateIPs))
				return False
		if (self.HostName != comparisonObject.HostName):
			if (multiLogger):
				multiLogger.debug('Host names do not match ("{0}", "{1}")'.format(self.HostName, comparisonObject.HostName))
			return False
		if (includeHostAliases):
			if (self.HostAliases != comparisonObject.HostAliases):
				if (multiLogger):
					multiLogger.debug('Host aliases do not match ("{0}", "{1}")'.format(self.HostAliases, comparisonObject.HostAliases))
				return False
		if (self.HostFQDN != comparisonObject.HostFQDN):
			if (multiLogger):
				multiLogger.debug('Host FQDNs do not match ("{0}", "{1}")'.format(self.HostFQDN, comparisonObject.HostFQDN))
			return False
		if (includePort):
			if (self.Port != comparisonObject.Port):
				if (multiLogger):
					multiLogger.debug('Ports do not match ("{0}", "{1}")'.format(self.Port, comparisonObject.Port))
				return False
		return True
		
class Socket():
	def __init__(self):
		self.Layer3Address = Layer3Address()
		self.Socket = None