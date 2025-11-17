# Gilon Kraft
# LETREP26 - Software Subteam
# Date Started: 11/15/2025

from tkinter import Tk
from tkinter.filedialog import askopenfilename
import matplotlib.pyplot as plt
import os
import numpy as np
import pandas

''' Program takes in a data file from the Pizeoelectric Force sensor.
The data is then divided into chunks of 250 data points. 
Each chunk is then averaged and stored in an array.
The result has the same number of samples as the EMG sensors making comparison easy'''

# --- 1. Get the file path ---
Tk().withdraw()
file_path = askopenfilename()

if not file_path:
    print("You canceled. Stopping.")
else:
    print(f"File path selected: {file_path}")

    # --- 2. Read the file ---
    my_data = pandas.read_csv(file_path)
    print("--- SUCCESS! File read. ---")

    try:
        # --- 3. Convert 'Force Reading" column to numbers ---
        # Any text that can't be converted will become 'NaN'
        my_data["Force Reading"] = pandas.to_numeric(
            my_data["Force Reading"], errors="coerce"
        )
        # --------------------------

        # --- 4. Get length and chunk size ---
        dataPoints = my_data.shape[0]
        chunk_size = 250    

        # --- 5. Create the grouping key ---
        grouping_key = np.arange(dataPoints) // chunk_size

        # --- 6. Group and average (this will now work) ---
        scaled_data = my_data["Force Reading"].groupby(grouping_key).mean()    
        
    except KeyError:
        print("\nERROR: 'Force Reading' column not found.")
        print(f"Columns available are: {my_data.columns.tolist()}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

# Showing a Graph of the Force Data
plt.plot(averaged_scaling)
plt.show()

# Generating a filename for scaled data and saving data to csv
file_name = os.path.basename(file_path)
file_name = "scaled_" + file_name 
np.savetxt(file_name, averaged_scaling, delimiter=',', fmt='%d')