from tkinter import Tk
from tkinter.filedialog import askopenfilename

import numpy as np
import pandas

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
        # --- 3. THIS IS THE FIX ---
        # Convert the 'Force Reading' column to numbers.
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
        averaged_scaling = my_data["Force Reading"].groupby(grouping_key).mean()

        # --- 7. Print your new averages ---
        print("\n--- Averaged Data Chunks ---")
        print(averaged_scaling)

    except KeyError:
        print("\nERROR: 'Force Reading' column not found.")
        print(f"Columns available are: {my_data.columns.tolist()}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

plt.plot(averaged_scaling)
