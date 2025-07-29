from scheduler.scheduler import Scheduler
from networking.serverrequesthandler import ServerRequestHandler

class WebApp:
    def __init__(self,name:str,baseDir:str,basePath:str, serverRequestHandler:ServerRequestHandler, scheduler:Scheduler):
        self.name=name
        self.baseDir=baseDir
        self.basePath=basePath
        self.serverRequestHandler = serverRequestHandler
        self.scheduler = scheduler