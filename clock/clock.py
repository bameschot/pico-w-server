from env.env import *
import time

def getCurrenS()->int:
    return time.time()

def tickMs()->int:
    if IS_MICRO_PYTHON:
        return time.ticks_ms()
    else:
        return time.time_ns()/1000000
