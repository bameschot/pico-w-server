from env.env import *

if IS_MICRO_PYTHON:
    from machine import Pin
    import network
    
    from networking.wireless import Wireless

import platform
import time
import asyncio
import socket
import gc
import ssl
import sys

#from ssl import SSLContext
from logs.log import *
from networking.serverrequesthandler import ServerRequestHandler,StaticResouceRequestHandler,CORSPreflightRequestHandler
from networking.server import Server
from scheduler.scheduler import Scheduler, ScheduledTask
from apps.picothreads.picothreads import *
from apps.serveradmin.serveradmin import *
from apps.usermanagement.usermanagement import *

from config.serverconfig import *


class ToggleLedTask(ScheduledTask):
    def __init__(self,blinkInterval:int=1):
        super().__init__("togle-led", 0, blinkInterval ,True)
        if IS_MICRO_PYTHON:
            self.led = Pin("LED", Pin.OUT)
    
    async def execute(self):
        if IS_MICRO_PYTHON:
            self.led.toggle()

class RunGCTask(ScheduledTask):
    def __init__(self):
        super().__init__("run-gc", 0, 6, True)
    
    async def execute(self):
        gc.collect()
        if IS_MICRO_PYTHON:
            print ('Free memory: '+ str(gc.mem_free()))

#Main 
async def main():
    log('--------------Starting pico w--------------')    
    
    loadServerConfig()
    
    scheduler = Scheduler()

        
    serverRequestHandler = ServerRequestHandler()

    #--------------------
    #|Server setup
    #--------------------

    
    
    #connect wireless
    serverConfig = getServerConfig()
    blinkInterval=1
    time.sleep(3)
    ip = ''
    
    if IS_MICRO_PYTHON:
        wireless = Wireless()
        
        if(serverConfig.preferredConnectionMode == "AP"):
            wireless.connect(network.AP_IF,serverConfig.apSSID,serverConfig.apPassword)
            blinkInterval=5
        else:
            try:
                wireless.connect(network.STA_IF,serverConfig.staSSID,serverConfig.staPassword)
                blinkInterval=1
            except Exception as e:
                print("Wireless Exception: "+str(e))
                sys.print_exception(e)
                
                log("Failed to connect to STA network "+serverConfig.staSSID+ ". Setting up AP: "+serverConfig.apSSID +"/"+serverConfig.apPassword+"/"+serverConfig.apIp )
                wireless.connect(network.AP_IF,serverConfig.apSSID,serverConfig.apPassword,serverConfig.apIp)
                blinkInterval=5
        ip = wireless.ip
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('192.255.255.255', 1))
            ip = s.getsockname()[0]
        except:
            ip = '0.0.0.0'
        finally:
            s.close()
    

    server = Server(ip,serverRequestHandler)
    
    
    #SSL is unfeasebly slow for pico-w, just leave it in for reference 
    if serverConfig.protocol == 'https' :
        #setup ssl context
        sslContext = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        
        if IS_MICRO_PYTHON:
            sslContext.verify_mode = ssl.CERT_NONE
        else:
            #sslContext.verify_mode = ssl.VerifyMode.CERT_REQUIRED
            pass
        
        #sslContext.load_cert_chain("./certs/ec_cert.der", "./certs/ec_key.der")
        extention = '.pem'
        if IS_MICRO_PYTHON:
            extention = '.der'
        sslContext.load_cert_chain("./certs/rsa_cert"+extention, "./certs/rsa_key"+extention)
        
        #start request handler
        asyncio.create_task(asyncio.start_server(server.handleRequest, "0.0.0.0", 443,backlog=20,ssl=sslContext))
    else:
        #start request handler
        asyncio.create_task(asyncio.start_server(server.handleRequest, "0.0.0.0", 80,backlog=20))
    
    print('pico server running on: '+ip + ' protocol: '+serverConfig.protocol)
    
    #--------------------
    #|App setup
    #--------------------

    #handle CORS preflight (effectively disables all other OPTIONS request paths)        
    serverRequestHandler.add(CORSPreflightRequestHandler(disableCORS = True))


    #apps
    picoThreads = PicoThreadsApp(serverRequestHandler,scheduler,ip,serverConfig.protocol)
    serverAdmin = ServerAdminApp(serverRequestHandler,scheduler,ip,serverConfig.protocol)
    userManagement = UserManagementApp(serverRequestHandler,scheduler,ip)

    
    #shared static resource handlers
    serverRequestHandler.add(StaticResouceRequestHandler("./apps",""))
    serverRequestHandler.add(RawStaticResourceBodyWriter("./apps",""))

    #scheduler
    scheduler.schedule(RunGCTask())
    scheduler.schedule(ToggleLedTask(blinkInterval))

    
    log('Server is ready')
    
    #scheduler loop also keeps the server alive
    await scheduler.start()


try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()
