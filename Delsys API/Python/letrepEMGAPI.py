# Gilon Kraft
# LETREP26 - Software Subteam
# Date Started: 11/14/2025

"""This program implements the Delsys API
First, it establishes a connection with the EMG sensors"""

import sys

# Import the *correct* class names
from AeroPy.DataManager import DataManager  # <-- FIX 1: The class is DataManager
from AeroPy.TrignoBase import TrignoBase

# --- This is the correct 3-step setup ---

# Step 1: Create the DataManager.
# We pass 'None' for the plot object.
dataHandler = DataManager(None)  # <-- FIX 2: Use DataManager

# Step 2: Create the TrignoBase and give it the handler.
base = TrignoBase(dataHandler)

# Step 3: Complete the circular dependency.
# Tell the DataManager's DataKernel about the 'base' object.
dataHandler.DataKernel.TrigBase = base

# --- Your original logic, corrected ---

# The correct property is 'TrigBase' (capital T)
TrigBase = base.TrigBase

# Call the connection method *on the 'base' object*
print("Connecting to base...")
base.Connect_Callback()
print("Connection complete.")

# You can now use 'base' to do things
# base.Scan_Callback()
