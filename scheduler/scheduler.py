import asyncio

SCHEDULER_TICK_INTERVAL = 1

class ScheduledTask(object):
    def __init__(self,name:str, tick:int=0,interval:int=60,repeating:bool=True):
        self.name = name
        self.interval = interval
        self.tick = tick
        self.repeating = repeating
        
    async def handleTick(self) -> bool:
        if self.tick == self.interval:
            await self.execute()
            self.tick = 0
            if self.repeating:
                return False
            return True
        else:
            self.tick+=1
            return False
        
    async def execute(self):
        pass


class Scheduler:
    def __init__(self):
        self.tasks:List[ScheduledTask] = []
        self.running = True
        self.currentTick = 0
    
    def schedule(self,task:ScheduledTask):
        print("scheduled: "+task.name+" interval: "+str(task.interval) + " repeat: "+str(task.repeating))
        self.tasks.append(task)
    
    async def checkAndRunTasks(self):
        ts = self.tasks
        tsd = []
        #check and handle the tick for each task
        for i in range(0,len(ts)):
            if await ts[i].handleTick():
                tsd.append(i)
        #remove tasks that are finalized
        for i in tsd:
            print("removed task: "+ts[i].name) 
            ts.pop(i)
            
        #for task in self.tasks:
        #    if await task.handleTick():
        #        print("remove")
            
    async def start(self):
        while True:
            await self.checkAndRunTasks()   
            await asyncio.sleep(SCHEDULER_TICK_INTERVAL)