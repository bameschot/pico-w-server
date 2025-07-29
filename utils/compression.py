from env.env import *
#IS_MICRO_PYTHON = False
import io
if IS_MICRO_PYTHON:
    import deflate
else:
    import zlib

COMPRESSION_W_BITS = 9


def uncompressStreamToStream(compressedStream) -> bytearray:
    if IS_MICRO_PYTHON:
        return deflate.DeflateIO(compressedStream, deflate.ZLIB)
    else:
        return io.BytesIO(zlib.decompress(compressedStream.read()))#, -1, COMPRESSION_W_BITS)
    
def compressStreamFromStream(uncompressedBytes:bytearray) -> bytearray:

    if IS_MICRO_PYTHON:
        stream = io.BytesIO()
        with deflate.DeflateIO(stream, deflate.ZLIB) as d:
            d.write(uncompressedBytes)
        return stream.getvalue()
    else:
        return zlib.compress(uncompressedBytes,level=-1,wbits=COMPRESSION_W_BITS)
    

def uncompress(compressedBytes:bytearray) -> bytearray:
    if IS_MICRO_PYTHON:
        return uncompressStreamToStream(io.BytesIO(compressedBytes)).read()
    else:
        return zlib.decompress(compressedBytes)#, -1, COMPRESSION_W_BITS)
    
def compress(uncompressedBytes:bytearray) -> bytearray:

    if IS_MICRO_PYTHON:
        stream = io.BytesIO()
        with deflate.DeflateIO(stream, deflate.ZLIB) as d:
            d.write(uncompressedBytes)
        return stream.getvalue()
    else:
        return zlib.compress(uncompressedBytes)#, -1, COMPRESSION_W_BITS)
    
def stringToBytes(data)->bytearray:
    return data.encode('utf-8')

def bytesToString(data:bytearray)->str:
    return data.decode('utf-8')

def compressStringToFile(data:str,filePath:str):
    with open(filePath, "wb") as f:
        f.write(compress(stringToBytes(data)))
        
def uncompressFileToString(filePath:str):
    with open(filePath, "rb") as f:
        return bytesToString(uncompress(f.read()))
    
def compressFileToFile(fileInPath:str,fileOutPath:str):
    with open(fileInPath, "rb") as inf:
        with open(fileOutPath, "wb") as ouf:
            ouf.write((compress(inf.read())))

# if IS_MICRO_PYTHON == False:
#     compressFileToFile('v86.wasm','v86.wasm.gz')
#     compressFileToFile('v86_all.js','v86_all.js.gz')
#     compressFileToFile('seabios.bin','seabios.bin.gz')
#     compressFileToFile('vgabios.bin','vgabios.bin.gz')
#     compressFileToFile('libv86.js','libv86.js.gz')
    
#    compressStringToFile('all cats are hands-on !','test1.gz')

#with open('test1.gz', "rb") as f:
#    print(uncompressStreamToStream(f).read())

#print(uncompressFileToString('test1.gz'))


