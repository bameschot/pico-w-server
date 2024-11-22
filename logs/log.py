import time

LOG_FILE = "./logs/files/log.txt"

def log(line:str):
    print(line)
    with open(LOG_FILE,'a') as f:
        f.write("["+str(time.time())+"] "+line+'\n')