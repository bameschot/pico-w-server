import deflate
import io
#import zlib

COMPRESSION_W_BITS = 21 #gzip

def uncompress(compressedBytes:bytearray) -> bytearray:
    #return zlib.compress(compressedBytes, wbits=COMPRESSION_W_BITS)
    with deflate.DeflateIO(io.BytesIO(compressedBytes), deflate.ZLIB) as d:
        return d.read()
    
def compress(uncompressedBytes) -> bytearray:
    #return zlib.decompress(uncompressedBytes, wbits=COMPRESSION_W_BITS)
    stream = io.BytesIO()
    with deflate.DeflateIO(stream, deflate.ZLIB) as d:
        d.write(uncompressedBytes)
    return stream.getvalue()
    
def stringToBytes(data:String)->bytearray:
    return data.encode('utf-8')

def bytesToString(data:bytearray)->str:
    return data.decode('utf-8')

def compressStringToFile(data:str,filePath:str):
    with open(filePath, "wb") as f:
        f.write(compress(stringToBytes(data)))
                
#compressStringToFile('cool dogs are nice cats!','file.gz') 
