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

import splunk.admin as admin
import splunk.entity as en
 
class ConfigApp(admin.MConfigHandler):
   def setup(self):
     if self.requestedAction == admin.ACTION_EDIT:
       for myarg in ['bamip', 'username', 'password']:
         self.supportedArgs.addOptArg(myarg)
 
   def handleList(self, confInfo):
     confDict = self.readConf("appsetup")
     if None != confDict:
       for stanza, settings in confDict.items():
         for key, val in settings.items():
           if key in ['bamip', 'username', 'password'] and val in [None, '']:
             val = ''
           confInfo[stanza].append(key, val)
 
   def handleEdit(self, confInfo):
     name = self.callerArgs.id
     args = self.callerArgs
     self.writeConf('appsetup', 'app_config', self.callerArgs.data)
 
admin.init(ConfigApp, admin.CONTEXT_NONE)
