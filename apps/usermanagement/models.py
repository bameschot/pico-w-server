import json
from utils.json import *


class UserTokens(JsonSerializable,JsonDeserializable):
    def __init__(self):
        self.tokenMap={}
    
    def fromJson(jsonStr:str):
        u = UserTokens()
        if len(jsonStr) == 0:
            return u
        
        indict = json.loads(jsonStr)
        if "tokenMap" in indict:
            for userToken in indict["tokenMap"].values():
                ut = UserToken.fromJson(userToken)
                u.tokenMap[ut.token]=ut
        return u

class UserToken(JsonSerializable,JsonDeserializable):
    def __init__(self,token:str="",userId:str="",exp:int=0):
        self.token = token
        self.userId = userId
        self.exp = exp
    
    def fromJson(indict:dict):
        #indict = json.loads(jsonStr)
        u = UserToken()
        if "token" in indict:
            u.token = indict["token"]
        if "userId" in indict:
            u.userId = indict["userId"]
        if "exp" in indict:
            u.exp = indict["exp"]
        return u

class User(JsonSerializable,JsonDeserializable):
    def __init__(self,userId:str="",userName:str="",pw:str="",lastOnlineTs:int=""):
        self.userId = userId
        self.userName = userName
        self.pw = pw
        self.lastOnlineTs = lastOnlineTs
    
    def fromJson(jsonStr:str):
        indict = json.loads(jsonStr)
        u = User()
        if "userId" in indict:
            u.userId = indict["userId"]
        if "userName" in indict:
            u.userName = indict["userName"]
        if "pw" in indict:
            u.pw = indict["pw"]
        if "lastOnlineTs" in indict:
            u.lastOnlineTs = indict["lastOnlineTs"]
        return u

class UserMap(JsonSerializable,JsonDeserializable):
    def __init__(self):
        self.users:dict[str,User]={}
    
    def fromJson(jsonStr:str):
        u = UserMap()
        
        if len(jsonStr) == 0:
            return u
        
        indict = json.loads(jsonStr)
        if "users" in indict:
            for k,user in indict["users"].items():
                usr = User.fromJson(json.dumps(user))
                u.users[usr.userId] = usr
        return u

class Users(JsonSerializable,JsonDeserializable):
    def __init__(self,users):
        self.users=users
    
    def fromJson(jsonStr:str):
        u = Users()
        indict = json.loads(jsonStr)
        if "users" in indict:
            for user in indict["users"]:
                u.users.append(User.fromJson(user))
        return u
