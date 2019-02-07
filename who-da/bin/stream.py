#!/usr/bin/env python
#
# Copyright 2019 BlueCat Networks (USA) Inc. and its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import sys
import requests
from BAM import BAM

from splunklib.searchcommands import \
    dispatch, StreamingCommand, Configuration, Option, validators

# Using undocumented, internal splunk library to load configuration file
# https://answers.splunk.com/answers/69438/retrieve-configuration-items-from-a-custom-python-search-command.html
from splunk.clilib import cli_common

@Configuration()
class BluecatIdentityCommand(StreamingCommand):
    source = Option(require=True, validate=None)
    useful_fields = ['ip_macAddress', 'ip_leaseTime', 'ip_state', 'host_absoluteName', 'mac_name', 'net_name']
    ips = []

    def cacheAdd(self,update_record):
	self.ips.append(update_record)

    def cacheLookup(self,ipaddr):
	for i in range(0, len(self.ips)):
		if self.ips[i]["ip_address"] == ipaddr:
			return self.ips[i]
	return 0


    def stream(self, records):

	cfg = cli_common.getConfStanza("appsetup","app_config")
	bam = BAM(cfg.get("bamip"), cfg.get("username"), cfg.get("password"))
	bam.login()

	for record in records:
		if self.source in record:
			ipaddr = record[self.source]
			ipobj = self.cacheLookup(ipaddr)
			update_record = {}
			obj = {}

			if not ipobj:
				obj = bam.getIP4Address(ipaddr)
				if obj:
					ipobj = obj.values
					update_record.update(ipobj)

					# If no object found returns None
					hostname = obj.getLinkedHostRecord()
					if hostname:
						update_record.update(hostname.values)

					network = obj.getParent()
					if network:
						update_record.update(network.values)

					if "ip_macAddress" in ipobj:
						macobj = bam.getMACAddress(ipobj["ip_macAddress"])
						update_record.update(macobj.values)
						# Copy attributes from one Tag on MAC address object
						# MAC address objects are tagged with a user in Identity Bridge
						user = macobj.getLinkedTag()
						if user:
							update_record.update(user.values)

					self.cacheAdd(update_record)
			else:
				update_record = ipobj

			for key in self.useful_fields:
				if key in update_record:
					record[key] = update_record[key]
				else:
					record[key] = ""

		yield record

	bam.logout()
	return
	

dispatch(BluecatIdentityCommand, sys.argv, sys.stdin, sys.stdout, __name__)
