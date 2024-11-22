import json

SERVER_CONFIG_FILE = "./serverconfig.json"


class ServerConfig:
    def __init__(self,preferredConnectionMode:str="",protocol:str="",staSSID:str="",staPassword:str="",apSSID:str="",apPassword:str="",apIp:str=""):
        self.preferredConnectionMode = preferredConnectionMode
        self.protocol=protocol
        self.staSSID = staSSID
        self.staPassword = staPassword
        self.apSSID = apSSID
        self.apPassword = apPassword
        self.apIp = apIp
        
        
    def toJson(self)->str:
        return json.dumps(self.__dict__)
    
    def fromJson(jsonDict:dict):
        return ServerConfig(jsonDict["preferredConnectionMode"],jsonDict["protocol"],jsonDict["staSSID"],jsonDict["staPassword"],jsonDict["apSSID"],jsonDict["apPassword"],jsonDict["apIp"])

SERVER_CONFIG:ServerConfig


def loadServerConfig():
    with open(SERVER_CONFIG_FILE) as f:
        jsonDict = json.load(f)
        print("loaded server configuration: "+str(jsonDict))
        global SERVER_CONFIG
        SERVER_CONFIG = ServerConfig.fromJson(jsonDict)


def saveServerConfig():
    with open(SERVER_CONFIG_FILE, "w") as f:
        configJson = SERVER_CONFIG.toJson()
        print("saving server configuration: "+str(configJson))
        f.write(configJson)
        f.flush()

def getServerConfig()->ServerConfig:
    return SERVER_CONFIG

def setServerConfig(serverConfig:ServerConfig):
    global SERVER_CONFIG
    SERVER_CONFIG = serverConfig






