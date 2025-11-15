# Gilon Kraft
# LETREP26 - Software Subteam
# Date Started: 11/14/2025

"""This program implements the Delsys API
First, it establishes a connection with the EMG sensors"""

import sys

# Import the *correct* class names
from AeroPy.DataManager import DataKernel  # <-- FIX 1: The class is DataKernel
from AeroPy.TrignoBase import TrignoBase

# --- This is the correct 3-step setup ---

# Step 1: Create the TrignoBase *first*, but pass 'None' for the handler.
base = TrignoBase(None)

# Step 2: Create the DataKernel and pass it the 'base' object.
# This works now because 'base' is not None.
dataHandler = DataKernel(base)

# Step 3: Complete the circle by setting the handler on the 'base' object.
base.collection_data_handler = dataHandler

# --- Your original logic, corrected ---

# The correct property is 'TrigBase' (capital T)
TrigBase = base.TrigBase

# Call the connection method *on the 'base' object*
print("Connecting to base...")
base.Connect_Callback()
print("Connection complete.")

# You can now use 'base' to do things
# base.Scan_Callback()