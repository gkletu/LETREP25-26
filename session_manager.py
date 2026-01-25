#Session manager: (template)
#   use session type to determine number of trials per session.

#==================
# Imports
#==================
import os
import ctypes
import time


from datetime import datetime
from Python import letrepEMGAPI as api


# Import your API and ctype libraries
from Python import letrepEMGAPI as api
motorlibrary = ctypes.CDLL(path)    # change "path" to file path of the ctypes

def baseline_motors(entry_index):
    for i in range(49):                 #runs loop 50 times (0-49)
        i = i+1
        motorlibrary.function_in_library    # calls motor control thing
    
def normal_motors(entry_index):
    for i in range(74):                 #runs loop 75 times (0-74)
        i = i+1
        motorlibrary.function_in_library

def baseline_collection(entry_index):
    for i in range(49):
        i = i+1
        api.start_collect
        time.sleep(0.5) # pauses function for 0.5 seconds
        api.stop_collect

def normal_collection(enty_index):
    for i in range(74):
        i = i+1
        api.start_collect
        time.sleep(0.5)
        api.stop_collect
        