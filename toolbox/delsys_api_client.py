import xmlrpc.client
import tkinter as tk
from tkinter import simpledialog
import numpy as np
import pandas as pd
import time

server = xmlrpc.client.ServerProxy("http://192.168.1.2:8000")

def pair_sensors(window):
    
    sensor_number = simpledialog.askinteger(
        title="Pair a Sensor",
        prompt="Enter the sensor number (1-16):",
        parent=window
    )
    server.pair_sensors(sensor_number)
    
def start_collect():
    server.start_collect()

def scan_sensors():
    server.scan_sensors()
    
def stop_collect():
    result = server.stop_collect()
    
    samples = np.frombuffer(result["samples"].data, dtype = result["sample_dtype"])
    timestamps = np.frombuffer(result["timestamps"].data, dtype = result["time_dtype"])
    values = np.frombuffer(result["values"].data, dtype = result["value_dtype"])
    
    result = pd.DataFrame({
        "samples": samples,
        "time": timestamps,
        "value": values    
    })
    return result
    

