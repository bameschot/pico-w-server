import json
from utils.genutils import copyDict

class JsonSerializable:
    def toJson(self,exclude:list[str]=[],add:dict={},addParams:dict={}) -> dict:
        od = self.__dict__
        d = copyDict(od)
                
        for ak,av in add.items():
            d.update({ak:av(d,addParams)})
        
        for excludeKey in exclude:
            if excludeKey in d:
                d.pop(excludeKey)
                
        for k,v in d.items():
            if isinstance(v,JsonSerializable):
                d[k] = v.toJson(exclude,add,addParams)
            elif isinstance(v,list):
                d[k] = []
                for i in v:
                    if isinstance(i,JsonSerializable):
                        d[k].append(i.toJson(exclude,add,addParams))
                    else:
                        d[k].append(i)
            elif isinstance(v,dict):
                d[k] = {}
                for vk,vv in v.items():
                    if isinstance(vv,JsonSerializable):
                        d[k][vk] = vv.toJson(exclude,add,addParams)
                    else:
                        d[k][vk] = vv
        return d

class JsonDeserializable:
    def fromJson(jsonStr:str):
        pass

def jsonToDict(jsonStr:str)->dict:
    return json.loads(jsonStr)
