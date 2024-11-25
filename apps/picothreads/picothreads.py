from env.env import *

from scheduler.scheduler import Scheduler
from networking.serverrequesthandler import *
from networking.templateengine import *
from apps.webapp import WebApp
from apps.picothreads.threadsmanager import *
from exceptions.picoserverexceptions import *
from utils.json import *
from apps.usermanagement.usermanagement import *

if IS_MICRO_PYTHON:
    MAX_MESSAGE_SIZE = 512
else:
    MAX_MESSAGE_SIZE = 1024*25
    
if IS_MICRO_PYTHON:
    MAX_THREAD_SUBJECT_SIZE = 64
else:
    MAX_THREAD_SUBJECT_SIZE = 128
    
if IS_MICRO_PYTHON:
    LIST_THREADS_INTERVAL_MS = 10000
else:
    LIST_THREADS_INTERVAL_MS = 1500

if IS_MICRO_PYTHON:
    FETCH_USERS_INTERVAL_MS = 10000
else:
    FETCH_USERS_INTERVAL_MS = 1500
    
TOKEN_REFRESH_INTERVAL_MS = 10000 #((USER_TOKEN_LIFETIME_S)/10)*1000

class PicoThreads:
    def __init__(self):
        pass
    

class PicoThreadsPageRequestHandler(RequestHandler):
    def __init__(self,methodMatch:str,pathMatch:str,baseDir:str,basePath:str,ip:str,protocol:str):
        self.ip=ip
        self.protocol=protocol
        super().__init__(methodMatch,pathMatch,baseDir,basePath)
    
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        serverResponse.contentType = "text/html"
        serverResponse.body = renderTemplate(self.baseDir+'/web/templates/pico-threads.html',{
            'ip':self.ip,
            'protocol':self.protocol,
            'max-message-size':MAX_MESSAGE_SIZE,
            'max-subject-size':MAX_THREAD_SUBJECT_SIZE,
            'list-threads-interval-ms': LIST_THREADS_INTERVAL_MS,
            'fetch-users-interval-ms': FETCH_USERS_INTERVAL_MS,
            'token-refresh-interval-ms': TOKEN_REFRESH_INTERVAL_MS
            })


class PostNewThreadHandler(RequestHandler):
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        userId = USER_REPOSITORY.authenticateUserTokenFromHeader(serverRequest.headers)
        
        bodyDict = jsonToDict(serverRequest.body)

        subject = None
        by = None
        if "subject" in bodyDict and "by" in bodyDict:
            subject = bodyDict["subject"]
            by = bodyDict["by"]
        else:
            raise BadRequestException()
        
        if len(subject) > MAX_THREAD_SUBJECT_SIZE:
            raise BadRequestException()
        
        THREADS_MANAGER.newThreadF(by,userId,subject)

        serverResponse.contentType = "application/json"
        serverResponse.statusCode = 200
        serverResponse.bodyWriter = ThreadsBodyWriter(userId)

class PostNewMessageHandler(RequestHandler):
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):        
        userId = USER_REPOSITORY.authenticateUserTokenFromHeader(serverRequest.headers)
        
        bodyDict = jsonToDict(serverRequest.body)

        threadId = serverRequest.pathParameters['threadId']
        
        text = None
        by = None
        if "text" in bodyDict and "text" in bodyDict:
            text = bodyDict["text"]
            by = bodyDict["by"]
        else:
            raise InternalServerErrorException()
        
        if len(text) > MAX_MESSAGE_SIZE:
            raise BadRequestException()
        
        
        THREADS_MANAGER.newMessageThreadF(threadId,by,userId,text)

        serverResponse.contentType = "application/json"
        serverResponse.statusCode = 200
        serverResponse.bodyWriter = ThreadsBodyWriter(userId)
        

class PostUpdateMessageHandler(RequestHandler):
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):        
        userId = USER_REPOSITORY.authenticateUserTokenFromHeader(serverRequest.headers)
        
        bodyDict = jsonToDict(serverRequest.body)
        
        threadId = serverRequest.pathParameters['threadId']
        messageId = serverRequest.pathParameters['messageId']
        
        text = None
        if "text" in bodyDict:
            text = bodyDict["text"]
        else:
            raise InternalServerErrorException()
        
        if len(text) > MAX_MESSAGE_SIZE:
            raise BadRequestException()
                
        THREADS_MANAGER.UpdateMessageThreadF(threadId,messageId,text)
        
        serverResponse.contentType = "application/json"
        serverResponse.statusCode = 200
        serverResponse.bodyWriter = ThreadsBodyWriter(userId)



class GetListThreadsHandler(RequestHandler):
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        userId = USER_REPOSITORY.authenticateUserTokenFromHeader(serverRequest.headers)

        serverResponse.contentType = "application/json"
        serverResponse.statusCode = 200
        serverResponse.bodyWriter = ThreadsBodyWriter(userId)


class ThreadsBodyWriter(BodyWriter):
    def __init__(self,userId):
        self.userId=userId
                
    def write(self,awriter):
        THREADS_MANAGER.readWriteThreads(awriter)
        
        #write(awriter,retrieveThreadsJson(self.userId))

def isMadeBySelf(jsonDict:dict,addParams:dict)->str:
        if 'byId' in jsonDict:
            return jsonDict['byId'] == addParams['userId'] 
        elif 'startedById' in jsonDict:
            return jsonDict['startedById'] == addParams['userId'] 
        else:
            return False
        
def retrieveThreadsJson(userId:str)->str:
   
    threads = THREADS_MANAGER.listThreadsF()
    
    threadsJson = str(json.dumps(threads.toJson(
            exclude = ['startedById','byId'],
            add = {'createdBySelf': isMadeBySelf},
            addParams = {'userId':userId}
        )))
    del threads
    
    return threadsJson


class PicoThreadsApp(WebApp):
    def __init__(self, serverRequestHandler:ServerRequestHandler, scheduler:Scheduler, ip:str,protocol:str):
        super().__init__("pico-threads","./apps/picothreads","/pico-threads",serverRequestHandler,scheduler)
        
        #Handlers
        serverRequestHandler.add(StaticResouceRequestHandler(self.baseDir,self.basePath))
 

        serverRequestHandler.add(PostUpdateMessageHandler("POST","\/threads\/.*\/messages\/.*",self.baseDir,self.basePath,{'threadId':3,'messageId':5}))
        serverRequestHandler.add(PostNewMessageHandler("POST","\/threads\/.*\/messages",self.baseDir,self.basePath,{'threadId':3}))
        
        serverRequestHandler.add(GetListThreadsHandler("GET","\/threads",self.baseDir,self.basePath))
        serverRequestHandler.add(PostNewThreadHandler("POST","\/threads",self.baseDir,self.basePath))

        serverRequestHandler.add(PicoThreadsPageRequestHandler("GET","",self.baseDir,self.basePath,ip,protocol))

        
        print("Started: "+self.name) 
        
