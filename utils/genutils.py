import random
import binascii
import hashlib

def mapListToDict(lst:list[str],seperator:str)->dict:
    p = {}
    for val in lst:
        kv = val.split(seperator)
        p[kv[0]]=kv[1]
    return p

def copyDict(d)->dict:
    c = {}
    for k,v in d.items():
        c[k]=v
    return c

def stringToBytes(data:str)->bytearray:
    return data.encode('utf-8')

def bytesToString(data:bytearray)->str:
    return data.decode('utf-8')

def decodeBase64(base64Str:str)->bytearray:
    return binascii.a2b_base64(base64Str)

def encodeBase64(base64Bytes:bytearray)->str:
    return bytesToString(binascii.b2a_base64(base64Bytes))[:-1]

def randomBytes(sizeBytes:int=32):
    bits = sizeBytes*8
    b = bytearray(0) 
    while bits>0:
        wordBits = max(bits%32,32)
        b+=random.getrandbits(wordBits).to_bytes(int(wordBits/8),'big')
        bits-=wordBits
    return b

def uniqueId(sizeBytes:int=16)->str:
    return encodeBase64(randomBytes(sizeBytes))

def sha256(data:bytearray)->bytearray:
    digest = hashlib.sha256(data)
    return digest.digest()
