import json

from scheduler.scheduler import Scheduler, ScheduledTask
from networking.serverrequesthandler import ServerRequest,ServerResponse,ServerRequestHandler, RequestHandler, StaticResouceRequestHandler
from exceptions.picoserverexceptions import *
from networking.templateengine import *
from apps.webapp import WebApp
from apps.usermanagement.models import *
from utils.json import jsonToDict
from utils.genutils import *
from clock.clock import *
from exceptions.picoserverexceptions import InternalServerErrorException

USER_FILE = './apps/usermanagement/storage/users.json'
USER_TOKEN_FILE = './apps/usermanagement/storage/user_tokens.json'
USER_TOKEN_LIFETIME_S = 36000

AUTHORIZATION_HEADER_NAME = 'Authorization'

class UserTokenRepository:
    def __init__(self):
        self.userTokens=None
    
    def createToken(self,userId:str)->str:
        userToken = UserToken(uniqueId(64),userId,getCurrenS()+USER_TOKEN_LIFETIME_S)
        self.userTokens.tokenMap[userToken.token] = userToken
        
        self.storeUserTokens()
        
        return userToken.token
        
    def validateUserAuthentication(self,token:str)->str:
        currentS = getCurrenS()
        if token in self.userTokens.tokenMap:
            userToken = self.userTokens.tokenMap[token]
            print('validating ' + token+ ' time left: '+str(userToken.exp-currentS)) 
            if userToken.exp > currentS:
                return userToken.userId
            else:
                del self.userTokens.tokenMap[token]
                self.storeUserTokens()
        return None
    
    def deleteUserAuthenticationById(self,userId:str):
        tokensToRemove = []
        for token in self.userTokens.tokenMap.values():
            if token.userId == userId:
                tokensToRemove.append(token.token)
        print(str(tokensToRemove))
        for t in tokensToRemove:
            del self.userTokens.tokenMap[t]
        
        self.storeUserTokens()
    
    def deleteUserAuthentication(self,token:str):
        if token in self.userTokens.tokenMap:
            del self.userTokens.tokenMap[token]
        self.storeUserTokens()
    
    def loadUserTokens(self):
        with open(USER_TOKEN_FILE,"r") as f:
            self.userTokens = UserTokens.fromJson(f.read())

    
    def storeUserTokens(self):
        with open(USER_TOKEN_FILE, "w") as f:
            json.dump(self.userTokens.toJson(),f)
            
    def deleteExpiredTokens(self):
        tokensToRemove = []
        currentS = getCurrenS()
        for token in self.userTokens.tokenMap.values():
            if token.exp <= currentS:
                tokensToRemove.append(token.token)
        print(str(tokensToRemove))
        for t in tokensToRemove:
            del self.userTokens.tokenMap[t]
        
        self.storeUserTokens()

USER_TOKEN_REPOSITORY = UserTokenRepository()
USER_TOKEN_REPOSITORY.loadUserTokens()

def getAuthorizationValueFromHeader(authType:str,headers:dict)->str:
    if not AUTHORIZATION_HEADER_NAME in headers:
            raise NotAuthorizedException('No Auth header found')
        
    authHeader = headers[AUTHORIZATION_HEADER_NAME]
    splitAutHeaderValue = authHeader.split(' ')

    if len(splitAutHeaderValue) != 2 and splitAutHeaderValue[0] != authType+' ':
        raise NotAuthorizedException('Header value not valid or auth type is not '+authType)
        
    return splitAutHeaderValue[1]



class UserRepository:
    def __init__(self):
        self.userMap:UserMap = UserMap()
        
        
    def identifyUser(self,name:str,pw:str)->str:
        for userId,user in self.userMap.users.items():
            print(user.userName + " == "+ name +" and "+ user.pw + " = "+pw) 
            if user.userName == name and user.pw == pw:
                return userId
        return None
        
        
    def registerUser(self,name:str,pw:str)->str:
        for userId,user in self.userMap.users.items():
            if user.userName == name:
                raise NotAuthorizedException('user with name: '+name+' already registered')
        
        user = User(uniqueId(),name,pw,getCurrenS())
        self.userMap.users[user.userId] = user
        self.saveUsers()
        print('registered user: '+name)
        return user.userId
    
    def refreshToken(self,userId:str)->str:
        return USER_TOKEN_REPOSITORY.createToken(userId)
        
    def loginUser(self,name:str,pw:str)->str:
        
        userId = self.identifyUser(name,pw)
        if userId == None:
            userId = self.registerUser(name,pw)
            
        self.userMap.users[userId].lastOnlineTs = getCurrenS()
        self.saveUsers()
        
        return USER_TOKEN_REPOSITORY.createToken(userId)
    
    def authenticateUserTokenFromHeader(self,headers:dict)->str:        
        return self.authenticateUserToken(getAuthorizationValueFromHeader('Bearer',headers))
        
        
    def authenticateUserToken(self,token:str)->str:
        userId = USER_TOKEN_REPOSITORY.validateUserAuthentication(token)
        
        if userId == None:
            raise NotAuthorizedException('User token not valid or not found')
        
        print('ping user: '+userId+ '='+str(getCurrenS()))
        self.userMap.users[userId].lastOnlineTs = getCurrenS()
        
        return userId
        
    def logoutUser(self,userId:str): 
        self.userMap.users[userId].lastOnlineTs = -1
        
        USER_TOKEN_REPOSITORY.deleteUserAuthenticationById(userId)
        print("Logging out user: "+userId)

        
    def listUsers(self)->Users:
        return Users(list(self.userMap.users.values()))
    
    def cleanupInactiveUsers(self):
        currentTs = getCurrenS()
        idsToRemove = []
        removedUsers = False
        
        for k,user in self.userMap.users.items():
            print("User removal check for "+ user.userName +":"+str(currentTs - user.lastOnlineTs) )
            #remove users that are inactive after 4 hours /10 days since the last ping
            if currentTs - user.lastOnlineTs > 864000:
                idsToRemove.append(k)
                removedUsers = True
                print("Removing inactive user: "+k)
                
        for k in idsToRemove:
            self.userMap.users.pop(k)
            
        if removedUsers:
            self.saveUsers()

                
    def loadUsers(self):
        with open(USER_FILE,"r+") as f:
            self.userMap = UserMap.fromJson(f.read())


    def saveUsers(self):
        with open(USER_FILE, "w+") as f:
            json.dump(self.userMap.toJson(),f)        
        

USER_REPOSITORY = UserRepository()
USER_REPOSITORY.loadUsers()

            
class CleanupInactiveUsersTask(ScheduledTask):
    def __init__(self):
        super().__init__("cleanup-inctive-users", 0, 60, True)
    
    async def execute(self):
        USER_REPOSITORY.cleanupInactiveUsers()
        
class CleanupExpiredTokensTask(ScheduledTask):
    def __init__(self):
        super().__init__("cleanup-expired-tokens", 0, 120, True)
    
    async def execute(self):
        USER_TOKEN_REPOSITORY.deleteExpiredTokens()
        
class SaveUsersTask(ScheduledTask):
    def __init__(self):
        super().__init__("save-users", 0, 65, True)
    
    async def execute(self):
        USER_REPOSITORY.saveUsers()


class PostLoginUserRequestHandler(RequestHandler):
    def processBasicAuthHeader(self,headers:dict):
        
        authHeaderValue = getAuthorizationValueFromHeader('Basic',headers)
        
        decodedBasicAuth = bytesToString(decodeBase64(authHeaderValue)).split(':')
        return [decodedBasicAuth[0],decodedBasicAuth[1]]
        
        
    
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        userCredentials = self.processBasicAuthHeader(serverRequest.headers)
        token = USER_REPOSITORY.loginUser(userCredentials[0],userCredentials[1])
        userId = USER_TOKEN_REPOSITORY.validateUserAuthentication(token)
        
        serverResponse.contentType = "application/json"
        serverResponse.statusCode = 200
        serverResponse.body = json.dumps({'token':token,'userId':userId})

class GetUsersRequestHandler(RequestHandler):
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        
        userId = USER_REPOSITORY.authenticateUserTokenFromHeader(serverRequest.headers)
        
        users = USER_REPOSITORY.listUsers()
        for i in range(0,len(users.users)):
            if users.users[i].userId == userId:
                users.users.pop(i)
                break                   
        
        serverResponse.contentType = "application/json"
        serverResponse.statusCode = 200
        serverResponse.body = str(json.dumps(users.toJson(exclude = ['pw','userId'])))
        
        users.users = None
        del users
        
class PostLogoutUserRequestHandler(RequestHandler):
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        userId = USER_REPOSITORY.authenticateUserTokenFromHeader(serverRequest.headers)

        USER_REPOSITORY.logoutUser(userId)
        
        serverResponse.contentType = "application/json"
        serverResponse.statusCode = 200
        serverResponse.body = ""
        
class GetRefreshUserTokenRequestHandler(RequestHandler):
    def handle(self,serverRequest:ServerRequest,serverResponse:ServerResponse):
        
        userId = USER_REPOSITORY.authenticateUserTokenFromHeader(serverRequest.headers)
        token = USER_REPOSITORY.refreshToken(userId)
        
        serverResponse.contentType = "application/json"
        serverResponse.statusCode = 200
        serverResponse.body = json.dumps({'token':token})


class UserManagementApp(WebApp):
    def __init__(self, serverRequestHandler:ServerRequestHandler, scheduler:Scheduler, ip:str):
        self.ip=ip
        super().__init__("user-management","./apps/usermanagement","/user-management",serverRequestHandler,scheduler)
        
        #scheduled jobs
        scheduler.schedule(CleanupInactiveUsersTask())
        scheduler.schedule(CleanupExpiredTokensTask())
        scheduler.schedule(SaveUsersTask())
        
        #Handlers
        serverRequestHandler.add(StaticResouceRequestHandler(self.baseDir,self.basePath))
        

        serverRequestHandler.add(PostLogoutUserRequestHandler("POST","/users/logout",self.baseDir,self.basePath))
        serverRequestHandler.add(PostLoginUserRequestHandler("POST","/users/login",self.baseDir,self.basePath))
        serverRequestHandler.add(GetRefreshUserTokenRequestHandler("GET","/users/refresh-token",self.baseDir,self.basePath))
        serverRequestHandler.add(GetUsersRequestHandler("GET","/users",self.baseDir,self.basePath))

        
        print("Started: "+self.name) 
    