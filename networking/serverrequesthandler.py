import re
from asyncio import StreamReader

from exceptions.picoserverexceptions import *
from networking.templateengine import *
from utils.compression import uncompressStreamToStream

class ServerRequest:
    def __init__(self):
        self.method=""
        self.path=""
        self.queryParameters={}
        self.pathParameters={}
        self.headers={}
        self.body=""
        
class ServerResponse:
    def __init__(self,awriter:StreamReader):
        self.awriter=awriter
        self.statusCode=200
        self.headers={}
        self.contentType = "text/html"
        self.disableCORS = True
        self.body=None
        self.bodyWriter=None #a BodyWriter object
        
    def commit(self):
        writeHttpFrame(self.awriter,self.statusCode)
        
        if self.disableCORS:
            self.headers["Access-Control-Allow-Origin"]="*"
            self.headers["Access-Control-Allow-Headers"]="*"
        self.headers["Content-type"] = self.contentType 
        writeHttpHeaders(self.awriter,self.headers)
        
        if self.body != None:
            writeHttpBody(self.awriter,self.body)
        elif self.bodyWriter != None:
            self.bodyWriter.write(self.awriter)

class BodyWriter:
    def __init__(self):
        pass
    
    def write(self,awriter:StreamReader):
        pass
    
class RequestHandler:
    def __init__(self,methodMatch:str,pathMatch:str,baseDir:str="./",basePath:str="",pathParameterMatches:dict={}):
        self.methodMatch=methodMatch
        self.basePath=basePath
        self.fullPathMatch=basePath+pathMatch
        self.baseDir=baseDir
        self.pathParameterMatches=pathParameterMatches
        
    def match(self,serverRequest:ServerRequest) -> bool:
        matches = self.methodMatch == serverRequest.method and re.search(self.fullPathMatch,serverRequest.path)
        if matches:
            pathSplit = serverRequest.path.split('/')
            
            for k,v in self.pathParameterMatches.items():
                if v >= len(pathSplit):
                    raise BadRequestException(details={'error':'path parameter index '+str(v)+' for parameter '+k+' is not in range of path elements '+ str(len(pathSplit))})
                serverRequest.pathParameters[k] = pathSplit[v]
            print('path parameters: '+str(serverRequest.pathParameters)) 
            return True
        else:
            return False
    
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        pass

class ServerRequestHandler:
    def __init__(self,handlers:list[RequestHandler]=[]):
        self.handlers = handlers
    
    def add(self,requestHandler:RequestHandler):
        print("added request handler: "+requestHandler.methodMatch+"; "+requestHandler.fullPathMatch) 
        self.handlers.append(requestHandler)
    
    def handleRequest(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        for handler in self.handlers:
            if handler.match(serverRequest):
                print("Matched+ "+serverRequest.method +"; "+serverRequest.path +" to "+handler.methodMatch+"; "+handler.fullPathMatch)
                handler.handle(serverRequest,serverResponse)
                return
            
        #nothing found, serve 404 not found
        raise NotFoundException()
        
class CORSPreflightRequestHandler(RequestHandler):
    def __init__(self,disableCORS:bool=True):
        self.disableCORS = disableCORS
        super().__init__("OPTIONS",'.*',"","")
     
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        if self.disableCORS:
            serverResponse.headers["Access-Control-Request-Method"]="DELETE, POST, GET, OPTIONS"
            serverResponse.headers["Access-Control-Allow-Origin"]="*"
            serverResponse.headers["Access-Control-Allow-Headers"]="*"
            serverResponse.headers["Access-Control-Allow-Private-Network"]="true"
            serverResponse.headers["Access-Control-Max-Age"]="600"
            serverResponse.headers["Access-Control-Allow-Credentials"]="true"
            
class StaticResourceBodyWriter(BodyWriter):
    def __init__(self,path):
        self.path=path
    
    def write(self,awriter):
        with open(self.path) as resourceFile:
            for line in resourceFile:
                write(awriter,line)

class RawStaticResourceBodyWriter(BodyWriter):
    def __init__(self,path):
        self.path=path
    
    def write(self,awriter):
        with open(self.path,"rb") as resourceFile:
            byte = resourceFile.read(1024)
            while byte != b"":
                writeBytes(awriter,byte)
                byte = resourceFile.read(1024)

class CompressedStaticResourceBodyWriter(BodyWriter):
    def __init__(self,path):
        self.path=path
    
    def write(self,awriter):
        with open(f"{self.path}.gz","rb") as resourceFile:
            compressedStream = uncompressStreamToStream(resourceFile)
            byte = compressedStream.read(1024)
            while byte != b"":
                writeBytes(awriter,byte)
                byte = compressedStream.read(1024)
                

class StaticResouceRequestHandler(RequestHandler):
    def __init__(self,baseDir:str,basePath:str):
        super().__init__("GET",'\/(css|js)\/.*\.(css|js)',baseDir,basePath)
     
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        #handle the request
        print("static resource: "+self.transformRequestToResourcePath(serverRequest.path)) 
        if bool(re.search('.*\.css', serverRequest.path)):
            serverResponse.contentType = 'text/css'
        elif bool(re.search('.*\.js', serverRequest.path)):
            serverResponse.contentType = 'text/javascript'

        #with open(self.transformRequestToResourcePath(serverRequest.path)) as resourceStream:
        #    serverResponse.body= resourceStream.read()
        
        serverResponse.bodyWriter = StaticResourceBodyWriter(self.transformRequestToResourcePath(serverRequest.path))
        
    
    def transformRequestToResourcePath(self,path:str)->str:
        if self.basePath == "":
            return self.baseDir+"/web"+path
        return self.baseDir+"/web"+path.split(self.basePath)[1]

class AnyResouceRequestHandler(RequestHandler):
    def __init__(self,baseDir:str,basePath:str):
        super().__init__("GET",'\/.*\.(.*)',baseDir,basePath)
     
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        #handle the request
        print("static resource: "+self.transformRequestToResourcePath(serverRequest.path)) 
        if bool(re.search('.*\.css', serverRequest.path)):
            serverResponse.contentType = 'text/css'
        elif bool(re.search('.*\.js', serverRequest.path)):
            serverResponse.contentType = 'text/javascript'
        
        serverResponse.bodyWriter = RawStaticResourceBodyWriter(self.transformRequestToResourcePath(serverRequest.path))
        
    
    def transformRequestToResourcePath(self,path:str)->str:
        if self.basePath == "":
            return self.baseDir+"/web"+path
        return self.baseDir+"/web"+path.split(self.basePath)[1]
    
class CompressedResouceRequestHandler(RequestHandler):
    def __init__(self,pathMatch:str,baseDir:str,basePath:str):
        super().__init__("GET",pathMatch,baseDir,basePath)
     
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        #handle the request
        print("compressed resource: "+self.transformRequestToResourcePath(serverRequest.path)) 
        if bool(re.search('.*\.css', serverRequest.path)):
            serverResponse.contentType = 'text/css'
        elif bool(re.search('.*\.js', serverRequest.path)):
            serverResponse.contentType = 'text/javascript'
        
        serverResponse.bodyWriter = CompressedStaticResourceBodyWriter(self.transformRequestToResourcePath(serverRequest.path))
        
    
    def transformRequestToResourcePath(self,path:str)->str:
        if self.basePath == "":
            return self.baseDir+"/web"+path
        return self.baseDir+"/web"+path.split(self.basePath)[1]
