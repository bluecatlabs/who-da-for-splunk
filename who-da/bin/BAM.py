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

import requests
from requests.auth import HTTPBasicAuth
import base64
import json

class BAM():

    def __init__ (self, ip, username, password):
    	self.url = 'http://' + ip + '/Services/REST/v1/' 
    	self.username = username
    	self.password = password
    	self.confid = 0
    	self.headers = {}

    def login(self):
        url = self.url + 'login?username=' + self.username + '&password=' + self.password
        response = requests.get(url)
	elements = str(response.text).split(' ')
        self.headers = { "Authorization" :  elements[2] + " " +  elements[3] }


    def restCall(self, call, data, json=0):
	url = self.url + call
	if json:
		headers = self.headers.update({ "Content-Type": "application/json" })
		response = requests.get(url, headers=headers)
	else:
		url += '?' + data
		response = requests.get(url, headers=self.headers)

	if(response != None):
		# For an error the response.content will be the error string in JSON format
		return response.content
	else:
		return None

    def getEntity(self, val, etype):
	# If value is zero or an empty string, return None
	if val=="" or val==str(0) or val==0:
		return None

	# Find the object based on type
	# Where there are multiple configurations, this searches all of them,
	# and only returns one of the results
	response = self.restCall('searchByObjectTypes', 'keyword='+val+'&types='+etype+'&start=0&count=1')
	ent = json.loads(response)
	if  isinstance(ent, list) and len(ent) > 0 and isinstance(ent[0], dict):
		return entity(self, ent[0], etype)
	else:
		return None

    def getIP4Address(self, val):
	return self.getEntity(val, 'IP4Address')

    def getMACAddress(self, val):
	return self.getEntity(val, 'MACAddress')

class entity:
    def __init__ (self, bam, obj, etype):
	self.bam = bam
	self.values = {}
	self.objprefix = ""
	if etype =='IP4Address':
		self.objprefix = "ip_"
	if etype =='IP4Network':
		self.objprefix = "net_"
	if etype =='MACAddress':
		self.objprefix = "mac_"
	if etype =='HostRecord':
		self.objprefix = "host_"
	if etype =='Tag':
		self.objprefix = "tag_"

	for key in obj:
		if obj[key] and key != "properties":
			self.values[self.objprefix + key] = obj[key]

	# If properties exists, split the properties and load them into values
	if 'properties' in obj:
		keyvals = obj['properties'].split('|')
		for attr in keyvals:
			if len(attr) > 1 :
				key, val = attr.split("=")
				self.values[self.objprefix + key] = val

    # The getLinked functions all return only one linked object,
    # where there could be more than one available
    def getLinkedEntity(self, etype):
	response = self.bam.restCall('getLinkedEntities', 'entityId='+str(self.values[self.objprefix+"id"])+'&type='+etype+'&start=0&count=1')
	ent = json.loads(response)
	if isinstance(ent, list) and len(ent) > 0 and isinstance(ent[0], dict):
		return entity(self.bam, ent[0], etype)
	else:
		return None

    def getLinkedTag(self):
	return self.getLinkedEntity('Tag')

    def getLinkedHostRecord(self):
	return self.getLinkedEntity('HostRecord')

    def getParent(self):
	response = self.bam.restCall('getParent', 'entityId='+str(self.values[self.objprefix+"id"]))
	ent = json.loads(response)
	if isinstance(ent, dict) and 'type' in ent:
		return entity(self.bam, ent, ent['type'])
	else:
		return None
