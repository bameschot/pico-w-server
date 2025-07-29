# pico-w-server

A webserver implemented in pure Micropyton for the Raspberry Pico W family of microntroller boards. 

## Overview

This project is meant to provide a working, fully editable, implementation of an asynchronous socket based web server that is able to serve basic web pages and implement basic rest services. This allows you to turn your $6 / €6.50 Raspberry Pico W into a low cost & low energy use webserver for your projects! Finally you can have a webserver that allows you to host a webpage for about 8 days on a 20000 mah powerbank :)  

Features of the webserver are:
  - Asynchronous, socket based, request / response handling.
  - Request / response abstraction layer that helps structuring web interfaces.
  - Inbuild scheduler that allows for repeating or one off tasks.
  - Module for handeling users with basic authentication.
  - Statically serves css, js and html files. Basic templating functionality for html files.
  - Handles CORS pre-flight requests (accepts all by default.)
  - Supports multiple web applications at once.
  - Runs both in micropyton on microcontrollers and vanilla Python on other platforms via a configurable flag.
  - Server can connect to an existing wifi network (STA) or serve as a standalone access point (AP). STA -> AP failover is supported when the STA connection fails. 
  - Management interface for server configuration settings
  - Comes with an example in the form of a micro social network / chat application to play around with!

Remarks:
  - For the purposes of security this is still a very basic webserver. Even tough SSL is technically possible (certainly when not running on your Pico with Micropython) this may still not cover all your security needs. When running without SSL remember that all the data transmitted over the network is not secure at all, even tough this may be fine for your application always consider the appropriate security measures when running your projects.
  - This is a hobby project so flaws and bugs will be present.
  - The default backbone css file is an unedited version of Simple CSS (https://simplecss.org/) also provided under the MIT licence.   

## Installing pico-w-server on your Pico W

In order to install pico-w-webserver on your board you first have to flash the board with the default Raspberry Pico W firmware as shown in this link: https://micropython.org/download/RPI_PICO_W/. 

After flashing your microcontroller you can connect it to an editor of your choice. Editors that work well are Thonny (https://thonny.org/) or Visual Studio Code (https://code.visualstudio.com/) with the Raspberry Pico extention (https://marketplace.visualstudio.com/items?itemName=raspberry-pi.raspberry-pi-pico) installed. 

You can now upload the all the folders in this repo (minus the readme and .gitignore) to the root of your Pico, as the imports rely on the structure of the folders as provided altering these may break the project on startup.

## Configuring pico-w-server

The webserver's network settings can can be configured via the ```serverconfig.json```file found in the root of the project. This file is re-loaded on startup so settings will take effect after resetting the microcontroller. The network related settings (connection mode  & sta/ap prefixed settings) only have an effect when the webserver runs on Micropython on a wifi enabled board. If the webserver runs on another platform in Python then the webserver will piggyback on the host device's network connection.  

The options that can be configured are:
  - **preferredConnectionMode**: Either _STA_ or _AP_ Determines the connection mode of the wireless module. Can be set to either STA (connecting to an existing wifi network) or AP (setting up a new wifi network for which the pico acts as an access point). When this setting is put to STA and the connection to the desired wifi network fails the the server will automatically fall back to setting itself up as an access point with the settings provided in this file. 
  - **staSSID**: The ssid of the wifi network that the webserver connects to when creating a connection in STA mode.
  - **staPassword**: The password of the wifi network that the webserver connects to when creating a connection in STA mode. Note that this password is stored in plain text.
  - **apSSID**: The ssid of the wifi network that the webserver sets up to when creating an access point in AP mode.
  - **apPassword**: The password of the wifi network that the webserver sets up when creating an access point in STA mode. Note that this password is stored in plain text.
  - **apIp**: The ip that the webserver tries to take when the connection mode is STA.
  - **protocol**: Either _http_ or _https_. Determines the desired protocol that the webserver communicates in. https attempts to setup a ssl connection when the correct certificate and key file are present, this setting is experimental for Micropython.

The webserver exposes a webpage that can be used to edit these settings on the url ```(http/https)://<ip>/server-admin```. Changing the settings here still requires a reset of the webserver. Note that this page is accessable to everyone who can access the pico. It can be disabled by removing the ```serveradmin``` app on startup.       

## Server runtime environment

The pico-w-server is primarily developed to be run on a microcontroller in a Micropython runtime. However in order to develop more easilly in absence of a microcontroller board or simply to work with a very basic webserver on another platform a environmental setting has been added to allow for the differences between Micropython and standard Python. By using the ```IS_MICRO_PYTHON``` variable the system can load or excecute Micropyton/Python specific code. 

for example Micropython specific imports can be loaded by adding:
```
if IS_MICRO_PYTHON:
    from machine import Pin
    import network
    
    from networking.wireless import Wireless
```

or Micropython specific code can be executed by adding:
```
if IS_MICRO_PYTHON:
        <execute Micropython specific code>
    else:
        <execute Python specific code>
```

## Webserver sockets and request response abstraction

The pico-w-server reads and writes network responses using it's asynchronous sockets. For ease of use this socket based communication is wrapped in an abstraction layer. As soon as a request is received the webserver reads it from the socket and extracts the request components from it (path, headers, body etc.) in a ```ServerRequest``` object. It then tries to match the request to a ```RequestHandler``` that provides an entry point for executing logic for the request. In this handler the response can be composed in ```ServerResponse``` object that is written to the outbound socket when comitted. 

This abstraction consists of the following components
  - RequestHandler
  - RequestHandler
  - ServerRequest
  - ServerResponse

### ServerRequest

The ServerRequest object contains the request details as received on the inbound socket. The elements of the request that are added in this object are:
 - http method
 - path
 - query parameters
 - path parameters
 - headers
 - body 

The path parameters are added to the ServerRequest object when the request is matched to a RequestHandler. 

### RequestHandler

The RequestHandler is the object that is used to match a ServerRequest to implementation logic. This object can be overridden to run logic when matched. The match is made on both the method and the path. The path match is performed via a regex which allows the matching to take query parameters and path parameters into account. 

As soon as the match is made the ```pathParameterMatches``` parameter is used to fill in the path parameters from the matched path into the ServerRequest. This is configured by providing a dict with the name of the parameter to extract as a key and the (1 based) index in the full path of the parameter to extract as the value. For example ```{'threadId':3}``` extracts the value ```44543``` from the path ```pico-threads/threads/44543/messages``` and registers it as a path parameter with key ```threadId```. 

This object also contains the base path and base directoru of the app the RequestHandler belongs to. 

An example of a RequestHandler that is overriden to execute logic is given below: 
```
class PostLogoutUserRequestHandler(RequestHandler):
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        userId = USER_REPOSITORY.authenticateUserTokenFromHeader(serverRequest.headers)

        USER_REPOSITORY.logoutUser(userId)
        
        serverResponse.contentType = "application/json"
        serverResponse.statusCode = 200
        serverResponse.body = ""
```

### ServerRequestHandler

The server request handler is the global matching engine that matches ServerRequests to RequestHandlers. All RequestHandlers need to be registered with the ServerRequestHandler to be found and each match is tested in the order the RequestHandler is registered. It is therefore important to register more specific matched before more broad matches. As the ServerRequestHandler is used for all apps and the webservers own generic RequestHandlers is can be important to consider the order in which apps are registered as well. 

An example of an app registering it's RequestHandlers with the ServerRequestHandler is given below:
```
serverRequestHandler.add(PostUpdateMessageHandler("POST","\/threads\/.*\/messages\/.*",self.baseDir,self.basePath,{'threadId':3,'messageId':5}))
serverRequestHandler.add(PostNewMessageHandler("POST","\/threads\/.*\/messages",self.baseDir,self.basePath,{'threadId':3}))
serverRequestHandler.add(GetListThreadsHandler("GET","\/threads",self.baseDir,self.basePath))
serverRequestHandler.add(PostNewThreadHandler("POST","\/threads",self.baseDir,self.basePath))
serverRequestHandler.add(PicoThreadsPageRequestHandler("GET","",self.baseDir,self.basePath,ip,protocol))
```

### ServerResponse

The ServerResponse object is used to compose a response that is comitted to the outbound socket when the request is fully handled. This commit process happens automatically by the webserver.  

The elements of the response that can be set are:
- A reference to the asynchrnous socket
- the response status code
- the response headers
- the response content type header, defaults to  ```text/html```
- an indicator for the browser to ignore CORS rules, defaults to ```true```
- Either:
  - The body to be written as a whole.
  - A BodyWriter object that writes the body to the outbound socket the moment the ServerResponse is comitted.

When writing the body 2 options are present. The first is that the body can be stored as a string in the ServerResponse as a whole, this is more convieniant but since the whole body remains in memory it may run into memory issues on Microcontrollers. In order to mitigate this the ServerResponse can also be provided a BodyWriter object. This is an object that overrides the ```BodyWriter``` class. When this object is provided the BodyWriter's ```write(self,awriter):``` is called. This method can be used to write content directly into the outbound socket after the correct protocol and header data has been written. Since this method gives direct access to the writer at the right moment data can be streamed directly from a source to the outbound socket without keeping all of it in memory. 

An example of the use of a bodywriter to stream data directly to the outbound socket is:
```
class StaticResourceBodyWriter(BodyWriter):
    def __init__(self,path):
        self.path=path
    
    def write(self,awriter):
        with open(self.path) as resourceFile:
            for line in resourceFile:
                write(awriter,line)
```

it can then be provided to the ServerResponse as given below:
```
serverResponse.bodyWriter = StaticResourceBodyWriter(self.transformRequestToResourcePath(serverRequest.path))
```

## Adding and setting up web applications

The pico-w-server is setup in such a way that is can run multiple web apps with some degree of functional seperation. Each web app can be registered in the webserver seperatly and has it's own base directory from where it can serve static resouces such as css, js and html as well as providing a way to structure the logic of the application and store data.

Each web app requires a object that derives from the ```WebApp``` class. This class handles the base directory, base path and references to the global ServerRequestHandler and Scheduler. This object can then be used to setup the required RequestHandlers and ScheduledTasks for the app. These apps can then be created  in ```main.py```after which they are available when the webserver has started. 

Each app has it's own directory in the ```app``` folder as indicated by the ```baseDir``` attribute of the WebApp. All paths in the RequestHandler are relative to this base directory. Static resources are served from the ```web``` folder in this base directory 

an example of the structure of multiple apps is given below:
```
/app
  /app1
    /web
      /css
        app1.css
      /js
        app1.js
      /templates
        app1.html
    app1.py
  /app2
    /web
      /css
        app2.css
      /js
        app2.js
      /templates
        app2.html
    app2.py
```


an example of how to subclass a WebApp and register the RequestHandlers and ScheduledTasks:
```
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

```

The way to register the apps in ```main.py```
```
    #--------------------
    #|App setup
    #--------------------

    #handle CORS preflight (effectively disables all other OPTIONS request paths)        
    serverRequestHandler.add(CORSPreflightRequestHandler(disableCORS = True))


    #apps
    picoThreads = PicoThreadsApp(serverRequestHandler,scheduler,ip,serverConfig.protocol)
    serverAdmin = ServerAdminApp(serverRequestHandler,scheduler,ip,serverConfig.protocol)
    userManagement = UserManagementApp(serverRequestHandler,scheduler,ip)
```

## Serving static resources and HTML templates

## Webserver Scheduler

The pico-w-server has a buildin scheduler that allows repeating tasks to be executed at a fixed interval or one off tasks after a specific amount of time. The scheduler itself is global to the webserver and executes tasks for the entire webserver, the scheduler is implemented in the ```Scheduler``` class. 

The scheduler works by advancing one tick for every second that passes. Each tasks is then checked agains the number of ticks defined as the task interval / execution delay. If the required number of ticks has elapsed the task is executed. One off tasks are then removed from the Scheduler's task list.

Tasks can be scheduled by creating an object of a subclass of the ```ScheduledTask``` class and adding it to the Scheduler's tasks list by calling the ```schedule``` method of the Scheduler. 

An example of two tasks being created and then added to the scheduler is given below:
```
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

#scheduler
scheduler.schedule(RunGCTask())
scheduler.schedule(ToggleLedTask(blinkInterval))

```


  
## Bundled v86 Emulator

The bundled v86 emulator is a compiled version courtesy of: 
https://github.com/copy/v86 

licenced as: 

Copyright (c) 2012, The v86 contributors
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.



