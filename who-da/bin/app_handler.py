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
