#Session manager: (template)
#   use session type to determine number of trials per session.

#==================
# Imports
#==================
import os
from datetime import datetime
import ctypes

# Import your API and ctype libraries
from Python import letrepEMGAPI as api
motorlibrary = ctypes.CDLL(path)

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
        #API Thing

def normal_collection(enty_index):
    for i in range(74):
        i = i+1
        #API Thing
        