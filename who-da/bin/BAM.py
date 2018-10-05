#
# Copyright 2018 BlueCat Networks (USA) Inc. and its affiliates
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
		return response.content
	else:
		return response

    def getConf(self, val):
	response = self.restCall('getEntityByName', 'parentId=0&type=Configuration&name=' + val)
	self.confid = json.loads(response)["id"]


    def getEntity (self, type, val):
	if (type == 'ip'):
		return entity(self, val, 'IP4Address')
	if (type == 'mac'):
		return entity(self, val, 'MACAddress')

class entity:
    def __init__ (self, bam, val, etype, copyobj=0):
	self.bam = bam
	self.values = {}
	self.properties = {}
	obj = {}
	
	self.objprefix = ""
	if etype =='IP4Address':
		self.objprefix = "ip_"
	if etype =='MACAddress':
		self.objprefix = "mac_"
	if etype =='HostRecord':
		self.objprefix = "host_"
	if etype =='Tag':
		self.objprefix = "tag_"

	#if not val:
	#	return obj

	# If value is zero, we return an empty entity object with id=0 and an empty propstr
	if val==str(0) or val==0:
		return self


	# If type was provided, We get the object based on the type.	
	# If type was not provided, we instantiate the object using the value passed in. 
	# This is when getLinkedEntity calls this to instantiate an object
	if copyobj==0:
		ent = self.bam.restCall('searchByObjectTypes', 'keyword='+val+'&types='+etype+'&start=0&count=1')
		if len(json.loads(ent)):
			obj = json.loads(ent)[0]
		else:
			return 
	else:
		obj = json.loads(val)[0]

	for key in obj:
		if obj[key]:
			if key != "properties":
				self.values[self.objprefix + key] = obj[key]
			else:
				self.properties = obj[key]

	# If properties exists, split the properties and load them into values
	if (self.properties):
		keyvals = self.properties.split('|')
		for attr in keyvals:
			if len(attr) > 1 :
				key, val = attr.split("=")
				self.values[self.objprefix + key] = val


    def getProperty(self, type):
	prop = self.propstr.split(type+'=')
	if len(prop) > 1:
		return prop[1].split('|')[0]
	else:
		return str(0)

    def getLinkedEntity(self, etype):
	res = 0
	response = self.bam.restCall('getLinkedEntities', 'entityId='+str(self.values[self.objprefix+"id"])+'&type='+etype+'&start=0&count=1')

	if "not supported" in str(response):
		return self
	
	if type(response)!='str' and len(json.loads(response)):
		return entity(self.bam, response, etype, 1)
	else:
		return self

class tag(entity):
    name = ""
    def __init__ (self, bam, val, type=0):

	if not type:
		tagobj = entity.__init__(self, bam, val, 'Tag')
	else:
		tagobj = entity.__init__(self, bam, val)

	if tagobj.id:
		self.name = val["name"]

class mac(entity):
    vendor = ""
    def __init__ (self, bam, val, type=0):

	if not type:
		macobj = entity.__init__(self, bam, val, 'MACAddress')
	else:
		macobj = entity.__init__(self, bam, val)

	if macobj.id:
		self.vendor = self.getProperty('macVendor')


class ip(entity):
    mac = 0
    lease = 0
    state = "STATIC"

    def __init__ (self, bam, val):
	ipobj = entity.__init__(self, bam, val, 'IP4Address')
	if ipobj.id:
		self.mac = self.getProperty('macAddress')
		self.lease = self.getProperty('leaseTime')
		self.state = self.getProperty('state')

    def getMAC(self):
	res = self.bam.restCall('getLinkedEntities', 'entityId='+str(self.id)+'&type=MACAddress&start=0&count=1')
	if res:
		return json.loads(res)[0]
	

    def getHostname(self, bam):
	hostname = ""
	res = bam.restCall('getLinkedEntities', 'entityId='+str(self.id)+'&type=HostRecord&start=0&count=1')
	if res:
		hostname = json.loads(res)[0]["properties"]
	
	return hostname

			
