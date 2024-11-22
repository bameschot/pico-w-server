import json
import os

from apps.picothreads.models import *
from utils.genutils import *
from clock.clock import *
from networking.templateengine import *

THREADS_STORAGE_FOLDER = "./apps/picothreads/storage/threads/"

class ThreadsManager:
    def __init__(self):
        pass
    
    def readWriteThreads(self,writer):
        threadIds = self.listThreadIds()
        idx = 1
        write(writer,'{"threads":[')
        for ti in threadIds:
            self.readWriteThread(writer,ti)
            if(idx<len(threadIds)):
                write(writer,',')
            
            idx+=1
        write(writer,']}')

    
    def readWriteThread(self,writer,threadId):
        with open(THREADS_STORAGE_FOLDER+threadId+".json", "rb") as f:
            while (b := f.read(100)):
                write(writer,bytesToString(b))
        
    
    def listThreadsF(self)->Threads:
        threads = Threads()
        threadIds = self.listThreadIds()
        for ti in threadIds:
            threads.threads.append(self.loadThread(ti))
        return threads
    
    def newThreadF(self,startedBy:str,startedById:str, subject:str):
        t = Thread(uniqueId(),startedBy,startedById,getCurrenS(),subject)
        self.storeThread(t)
        del t
    
    def newMessageThreadF(self,threadId:str, by:str,byId:str, text:str):
        thread = self.loadThread(threadId)
        m = Message(uniqueId(),by,byId,getCurrenS(),text)
        thread.messages.append(m)
        self.storeThread(thread)
        del m
        del thread
        
    def UpdateMessageThreadF(self,threadId:str,messageId:str, text:str):
        thread = self.loadThread(threadId)
        
        for m in thread.messages:
            if m.messageId == messageId:
                m.text=text
                m.editedTimestamp=getCurrenS()
        
        self.storeThread(thread)
        del thread
        
    def storeThread(self, thread:Thread):
        with open(THREADS_STORAGE_FOLDER+thread.threadId+".json", "w") as f:
            json.dump(thread.toJson(),f)
    
    def loadThread(self, threadId:str) -> Thread:
        with open(THREADS_STORAGE_FOLDER+threadId+".json", "r") as f:
            return Thread.fromJson(json.load(f))
        
    def listThreadIds(self)->list[str]:
        threadFiles = os.listdir(THREADS_STORAGE_FOLDER)
        threadIds = []
        for tf in threadFiles:
            threadIds.append(tf[:-5])
        return threadIds
        
    
THREADS_MANAGER = ThreadsManager()     
