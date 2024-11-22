import json
from utils.json import *

    
class Message(JsonSerializable,JsonDeserializable):
    def __init__(self,messageId="",by:str="",byId:str="",timestamp:int=-1,text:str=""):
        self.messageId=messageId
        self.by=by
        self.byId=byId
        self.timestamp=timestamp
        self.editedTimestamp = -1
        self.text=text
        
    def fromJson(indict:dict):
        m = Message()
        if "messageId" in indict:
            m.messageId = indict["messageId"]
        if "by" in indict:
            m.by = indict["by"]
        if "byId" in indict:
            m.byId = indict["byId"]
        if "timestamp" in indict:
            m.timestamp = int(indict["timestamp"])
        if "editedTimestamp" in indict:
            m.editedTimestamp = int(indict["editedTimestamp"])
        if "text" in indict:
            m.text = indict["text"]
        return m
        
class Thread(JsonSerializable,JsonDeserializable):
    def __init__(self,threadId="",startedBy:str="",startedById:str="",timestamp:int=-1,subject:str=""):
        self.threadId=threadId
        self.startedBy=startedBy
        self.startedById=startedById
        self.timestamp=timestamp
        self.subject=subject
        self.messages:List[Message] = []
        
    def fromJson(indict:dict):
        t = Thread()
        if "threadId" in indict:
            t.threadId = indict["threadId"]
        if "startedBy" in indict:
            t.startedBy = indict["startedBy"]
        if "startedById" in indict:
            t.startedById = indict["startedById"]
        if "timestamp" in indict:
            t.timestamp = int(indict["timestamp"])
        if "subject" in indict:
            t.subject = indict["subject"]
        if "messages" in indict:
            for msg in indict["messages"]:
                t.messages.append(Message.fromJson(msg))
        return t
            
class Threads(JsonSerializable,JsonDeserializable):
    def __init__(self):
        self.threads:list[Thread] = []
    
    def fromJson(indict:dict):
        t = Threads()
        if "messages" in indict:
            for thread in indict["threads"]:
                t.threads.append(Thread.fromJson(thread))
        return t
        



# threads = Threads()
# 
# t1 = Thread("Bas","44234ddf33",2343442,"Hello")
# t1.messages.append(Message("Bas","44234ddf33",3444323,"Who is going around asking cats to purr here?"))
# t1.messages.append(Message("Leon","87677gghg4333",3444353,"I dunno perhaps the soof"))
# t1.messages.append(Message("Sophie","erfer334234",3445553,"Not me! FU"))
# 
# threads.threads.append(t1)
# 
# s = str(json.dumps(threads.toJson()))
# print(str(s))
# 
# v = json.loads(s)
# print("---") 
# print(str(Threads.fromJson(v).threads[0].messages[0]))
