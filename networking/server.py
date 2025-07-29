from env.env import *

if not IS_MICRO_PYTHON:
    import traceback

import re
import io
import sys
import time
import json
from asyncio import StreamReader,StreamWriter

from networking.serverrequesthandler import ServerRequestHandler,ServerRequest,ServerResponse
from networking.templateengine import renderTemplate
from exceptions.picoserverexceptions import *
from clock.clock import *

from utils.genutils import mapListToDict

class Server:
    
    def __init__(self, ip:str,serverRequestHandler:ServerRequestHandler):
        self.ip = ip
        self.serverRequestHandler = serverRequestHandler
        
    async def handleRequest(self,areader:StreamReader,awriter:StreamWriter):
    
        print('Client connected on '+self.ip)
        start = tickMs()
        
        #Note this is still faster than reading content size
        #bufferSize = 1024*24
        #reader = io.BytesIO(await areader.read(bufferSize))
        
        
        try:
            #Read the first frame with the request information
            reader = areader
            request = await reader.readline()
            #print('request: '+request.decode("utf-8"))
            serverRequest = ServerRequest()
            serverResponse = ServerResponse(awriter)

            
            requestParts = request.decode("utf-8").split(' ')
            
            serverRequest.method = requestParts[0]
            print("RP: "+ str(requestParts))
            protocol = requestParts[2]
            
            fullRequestPath = requestParts[1].split('?')
            serverRequest.path = fullRequestPath[0]
            
            if len(fullRequestPath)>1:
                serverRequest.queryParameters = mapListToDict(fullRequestPath[1].split('&'),'=')
            
            # read header frames
            h = await reader.readline()
            while h != b'\r\n':
                header = h.decode("utf-8").split(': ')
                serverRequest.headers[header[0]]=header[1][:-2]
                h = await reader.readline()
                
            print('protocol: '+protocol[:-1])        
            print('method: '+serverRequest.method)
            print('path: '+serverRequest.path)
            print('query-parameters: '+str(serverRequest.queryParameters))
            print('headers: '+str(serverRequest.headers))
            
            # read body when a content length is given
            serverRequest.body = ''
            if 'Content-Length' in serverRequest.headers:
                cs = int(serverRequest.headers['Content-Length'])
                if cs > 0:
                    serverRequest.body =  (await reader.read(cs)).decode("utf-8")
            
            #done parsing request, close areader and reader
            if IS_MICRO_PYTHON:
                reader.close()    
            
            print('body: '+serverRequest.body)

            #then serve the custom (functional) paths
            self.serverRequestHandler.handleRequest(serverRequest,serverResponse)
                

        except PicoServerException as e:
            print("PicoServerException: "+str(e))
                                   
            if IS_MICRO_PYTHON:
                sys.print_exception(e)
            else:
                traceback.print_exc()
            
            #exception, serve error page based on exception
            serverResponse.statusCode = e.statusCode
            serverResponse.body = json.dumps(e.__dict__) #renderTemplate('./apps/web/templates/error.html',{'status-code':e.statusCode,'message':e.message,'details':e.details} )
        except Exception as e:
            print("Exception: "+str(e))
            ex = InternalServerErrorException(str(e))
            
            if IS_MICRO_PYTHON:
                sys.print_exception(e)
            else:
                traceback.print_exc()
            
            #exception, serve 500 internal server error
            serverResponse.statusCode = 500
            serverResponse.body = json.dumps(e.__dict__) #renderTemplate('./apps/web/templates/error.html',{'status-code':500,'message':'internal server error','details':str(e)} )
            
        
        #commit the response
        serverResponse.commit()
        await awriter.drain()
        #check if needed for micropython too
        awriter.close()
        await awriter.wait_closed()
        
        #help the gc a bit
        serverRequest.body = None
        serverRequest.headers = None
        serverRequest.queryParameters = None
        
        serverResponse.body = None
        serverResponse.headers = None        
        del serverResponse
        del serverRequest
        
        duration = tickMs()-start
        print("Client disconnected, duration: "+str(duration)+" ms")
        print("---------------------------------------------------")
        
    