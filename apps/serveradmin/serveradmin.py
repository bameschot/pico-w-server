from env.env import *

import json
import gc

if IS_MICRO_PYTHON:
    import machine

from scheduler.scheduler import Scheduler
from networking.serverrequesthandler import ServerRequest,ServerResponse,ServerRequestHandler, RequestHandler, StaticResouceRequestHandler
from networking.templateengine import *
from apps.webapp import WebApp
from config.serverconfig import *
from scheduler.scheduler import Scheduler, ScheduledTask, SCHEDULER_TICK_INTERVAL


class ServerStatus:
    def __init__(self,ip:str):
        self.uptime:int = 0
        self.ip = ip
    
    def freeMem(self)->int:
        if IS_MICRO_PYTHON:
            return gc.mem_free()
        else:
            return -1

class UptimeTask(ScheduledTask):
    def __init__(self,serverStatus:ServerStatus):
        self.serverStatus = serverStatus
        super().__init__("run-gc", 0, 1, True)
    
    async def execute(self):
        self.serverStatus.uptime+=SCHEDULER_TICK_INTERVAL

class GetServerConfigRequestHandler(RequestHandler):
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        serverResponse.contentType = "application/json"
        serverResponse.body = getServerConfig().toJson()
        
class PostServerConfigRequestHandler(RequestHandler):
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        setServerConfig(ServerConfig.fromJson(json.loads(serverRequest.body)))
        saveServerConfig()
        
        serverResponse.contentType = "application/json"
        serverResponse.body = ""

class PostRebootRequestHandler(RequestHandler):
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        print("Restarting Webserver")
        #machine.soft_reset()
        machine.reset()
        
        serverResponse.contentType = "application/json"
        serverResponse.body = ""
        
class GetServerStatusRequestHandler(RequestHandler):
    def __init__(self,methodMatch:str,pathMatch:str,baseDir:str="./",basePath:str="",serverStatus:ServerStatus=None):
        self.serverStatus = serverStatus
        super().__init__(methodMatch,pathMatch,baseDir,basePath)
    
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):        
        serverResponse.contentType = "application/json"
        serverResponse.body = '{"freeMemoryBytes": "'+str(self.serverStatus.freeMem())+'", "serverUptime": '+str(self.serverStatus.uptime)+', "freeStorage": "-1"}'

class GetIndexHandler(RequestHandler):
    def __init__(self,methodMatch:str,pathMatch:str,baseDir:str,basePath:str,ip:str,protocol:str):
        self.ip=ip
        self.protocol=protocol
        super().__init__(methodMatch,pathMatch,baseDir,basePath)

    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        serverResponse.contentType = "text/html"
        serverResponse.body = renderTemplate(self.baseDir+'/web/templates/admin.html',{'ip':self.ip,'protocol':self.protocol,'server-name':'pico-w-server'})        



class ServerAdminApp(WebApp):
    def __init__(self,serverRequestHandler:ServerRequestHandler, scheduler:Scheduler,ip:str,protocol:str):
        self.serverStatus=ServerStatus(ip)
        super().__init__("server-admin","./apps/serveradmin","/server-admin",serverRequestHandler,scheduler)
        
        #scheduled
        scheduler.schedule(UptimeTask(self.serverStatus))
        
        #Handlers
        serverRequestHandler.add(StaticResouceRequestHandler(self.baseDir,self.basePath))
        serverRequestHandler.add(GetServerConfigRequestHandler("GET","/config",self.baseDir,self.basePath))
        serverRequestHandler.add(PostServerConfigRequestHandler("POST","/config",self.baseDir,self.basePath))
        serverRequestHandler.add(GetServerStatusRequestHandler("GET","/status",self.baseDir,self.basePath,self.serverStatus))
        serverRequestHandler.add(PostRebootRequestHandler("POST","/reset",self.baseDir,self.basePath))

        serverRequestHandler.add(GetIndexHandler("GET","",self.baseDir,self.basePath,ip,protocol))

        print("Started: "+self.name)
