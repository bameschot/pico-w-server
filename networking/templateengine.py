from env.env import *

from asyncio import StreamReader
from utils.genutils import *
import gc

HTTP_HEADER_FRAME = 'HTTP/1.0 {{code}}\r\n'

HTTP_STATUS_CODES = {
    200: "200 OK",
    401: "401 Not Authorized",
    404: "404 Not Found",
    500: "500 Internal Server Error"
    }
    
def renderTemplate(templateName:str, parameters:dict) -> str:
    with open(templateName) as templateFile:
        template = templateFile.read()
        for key, value in parameters.items():
                template = template.replace('{{'+key+'}}',str(value))
                
        return template

def writeHttpFrame(awriter:StreamReader,code:int=200):
    write(awriter,HTTP_HEADER_FRAME.replace("{{code}}",HTTP_STATUS_CODES[code]))
    
def writeHttpHeaders(awriter:StreamReader,headers:dict):
    for k,v in headers.items():
        write(awriter,k+": "+v+"\r\n")
    write(awriter,"\r\n") 
        
def writeHttpBody(awriter:StreamReader,body:str):
    write(awriter,body)
    
def writeHttp(awriter:StreamReader,body:str,code:int=200,contentType="text/html"):
    writeHttpFrame(awriter,code)
    writeHttpHeaders(awriter,{"Content-type":contentType, "Access-Control-Allow-Origin":"*"})     
    write(awriter,body)
        
def serveHtml(awriter:StreamReader,template:str,parameters:dict,code:str="200 OK"):
    writeHttp(awriter,renderTemplate(template,parameters),code)

def serveStatic(resourceType:str, resourcePath:str, awriter:StreamReader):
    resourceContentType = 'text/css' if resourceType == 'css' else 'text/javascript'
    write(awriter,'HTTP/1.0 200 OK\r\nContent-type: '+resourceContentType+'\r\n\r\n')
    with open(resourcePath) as resource:
        write(awriter,resource.read())
        
def write(awriter:StreamReader,data:str):
    if IS_MICRO_PYTHON:
        awriter.write(data)
        awriter.drain()
    else:
        awriter.write(stringToBytes(data))

def writeBytes(awriter:StreamReader,data):
    if IS_MICRO_PYTHON:
        awriter.write(data)
        awriter.drain()
        gc.collect()
        print ('Free memory on write: '+ str(gc.mem_free()))
    else:
        awriter.write(data)
