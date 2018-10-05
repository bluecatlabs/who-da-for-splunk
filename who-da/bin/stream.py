#!/usr/bin/env python

import os
import sys
import requests
from BAM import BAM
from BAM import ip

from splunklib.searchcommands import \
    dispatch, StreamingCommand, Configuration, Option, validators

confval = {}
def getConfVals():
        appdir = os.path.dirname(os.path.dirname(__file__))
        localconfpath = os.path.join(appdir, "local", "appsetup.conf")
        for line in open(localconfpath).read().split("\n"):
                values = line.split("=")
                if len(values)>1:
                        confval[values[0].strip()] = values[1].lstrip()

@Configuration()
class BluecatIdentityCommand(StreamingCommand):
    source = Option(require=True, validate=None)
    ips = []

    def cacheAdd(self,update_record):
	self.ips.append(update_record)

    def cacheLookup(self,ipaddr):
	for i in range(0, len(self.ips)):
		if self.ips[i]["ip_address"] == ipaddr:
			return self.ips[i]
	return 0


    def stream(self, records):

	getConfVals()
	bam = BAM(confval["bamip"], confval["username"], confval["password"])
	bam.login()
	usefull_records = ['ip_macAddress', 'ip_leaseTime', 'ip_state', 'host_absoluteName']

	for record in records:
		present = 0
		ipaddr = record[self.source]
		ipobj = self.cacheLookup(ipaddr)
		update_record = {}
		obj = {}

		if not ipobj:
			obj = bam.getEntity('ip', ipaddr)
			if obj.values:
				hostname = obj.getLinkedEntity('HostRecord')
				ipobj = obj.values
				for key in ipobj:
					update_record[key] = ipobj[key]


				if "mac_macAddress" in ipobj:
					macobj = bam.getEntity('mac', ipobj["mac_macAddress"])
					user = macobj.getLinkedEntity('Tag')
					for key in macobj.values:
						update_record[key] = macobj.values[key]
					
				self.cacheAdd(update_record)
		else:
			update_record = ipobj

		for key in usefull_records:
			if key in update_record:
				record[key] = update_record[key]
			else:
				record[key] = "-"
		yield record
	return
	

dispatch(BluecatIdentityCommand, sys.argv, sys.stdin, sys.stdout, __name__)
