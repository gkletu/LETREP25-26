#Session manager: (template)
#   use session type to determine number of trials per session.

#==================
# Imports
#==================
import os
import ctypes
import time

from datetime import datetime
from serial_comm_Win import SerialComm

# Import API and ctype libraries
#from Python import letrepEMGAPI as api
## motorlibrary = ctypes.CDLL(path)    # change "path" to file path of the ctypes

def baseline_motors(entry_index):
    print(f"baseline_motors called with entry_index={entry_index}")  # Fixed debug line
    count = 0
    for i in range(50):  # Changed to 50 for clarity
        # motorlibrary.function_in_library
        count += 1
    print(f"baseline_motors finished, count={count}")  # Debug
    return count
    
def normal_motors(entry_index):
    print(f"normal_motors called with entry_index={entry_index}")  # Added debug
    count = 0
    for i in range(75):  # Changed to 75 for clarity
        # motorlibrary.function_in_library
        count += 1
    print(f"normal_motors finished, count={count}")  # Debug
    return count

#def baseline_collection(entry_index):
#    for i in range(49):
#        i = i+1
#        api.start_collect
#        time.sleep(0.5) # pauses function for 0.5 seconds
#        api.stop_collect

#def normal_collection(enty_index):
#    for i in range(74):
#        i = i+1
#        api.start_collect
#        time.sleep(0.5)
#        api.stop_collect
        