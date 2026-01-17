# Gilon Kraft
# LETREP26 - Software Subteam
# Date Started: 11/14/2025

"""This program implements the Delsys API
First, it establishes a connection with the EMG sensors"""

import sys
import tkinter as tk

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


# function to pair sensors
def pair_sensors():
    base.PairSensors(True)
    sensor_number = tkSimpleDialog.askinteger(
        title="Pair a Sensor", prompt="Enter the sensor number:"
    )
    base.PairSensor(sensor_number)


# function to scan for previously paired sensors
def scan_sensors():
    base.ScanSensors()

# function to initiate data collection
def start_collect():
    base.Configure(starttrigger = False, stoptrigger = False) # configures the sensor for data collection. we don't need triggering
    if base.IsPipelineConfigured():
        base.Start(ytdata = True) # starts data collection ytdata enables time stamps

# function to stop data collection
def stop_collect():
    base.Stop()
    data = base.PollYTData()
    return data
  
# Now we're going to build a GUI
window = tk.Tk()
window.title("LETREP26 Pair EMGs...")
window.geometry("960 x 540")

# Pair Sensors Button
pair_button = tk.Button(master=window, text="Pair Sensors", command=pair_sensors)
pair_button.pack()

# Scan Sensors Button
scan_button = tk.Button(master=window, text="Scan for Sensors", command=scan_sensors)
scan_button.pack()

# Start Collect Button
collect_button = tk.Button(master=window, text="Start Collection", command=start_collect)
collect_button.pack()

# Stop Collect Button
stop_button = tk.Button(master=window, text="Stop Collection", command=stop_collect)
stop_button.pack()

window.mainloop()
