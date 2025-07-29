import network
import time
import socket

from logs.log import *

class Wireless:
    def __init__(self):
        self.ssid = None
        self.password = None
        self.mode = None
        self.wlan = None
        self.status = None
        self.ip:str = ""
    
    

    def connect(self,mode:int,ssid:str,password:str,apIp:str="192.168.1.1"):
        self.mode = mode
        self.ssid = ssid
        self.password = password
        
        self.wlan = network.WLAN(mode)
        
        
        #connect for access point (AP_IF) or static access (STA_IF)
        if(self.mode == network.AP_IF):
            self.wlan.config(essid=ssid, password=password, pm = self.wlan.PM_NONE) # Disable power-save mode (for balance use PM_PERFORMANCE)
            self.wlan.ifconfig((apIp, '255.255.255.0', '192.168.0.1', '8.8.8.8'))
            self.wlan.active(True)
        else:
            self.wlan.config(pm = self.wlan.PM_NONE) # Disable power-save mode (for balance PM_PERFORMANCE)
            self.wlan.active(True)
            self.wlan.connect(ssid, password)


        
        log('Connecting to '+self.ssid+' in mode: '+str(self.mode))
        
        retries = 20
        while retries > 0:
            time.sleep(1)
            status = self.wlan.status()
            log('wlan status: '+str(status)+" retries left: "+str(retries))
            if self.wlan.isconnected():  #status < 0 or status > 3:
                break
            
            retries -= 1
        
        if self.wlan.status() != 3:
            raise RuntimeError('network connection failed')
        else:
            log('Wireless ready')
            self.status = self.wlan.ifconfig()
            self.ip = self.status[0]
            log('ip = ' + self.ip)
        
