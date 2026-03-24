# handles all the math, rectify, max, and threshold

import numpy as np
import pandas as pd
from scipy import signal

def analize_trial(emg_df, force_data, active_threshold=0):
    # Processes a single trial
    # emg_data: raw EMG dataframe
    # force_data: raw force data
    # active_threshold: 65% the baseline average for comparison

    # Extract list of EMG magnitude from EMG dataframe
    emg_values = emg_df["value"].tolist()
    emg_values = np.array(emg_values, dtype = float)
    emg_values = emg_values * 1000  # Convert Volts to Millivolts
    

    ## print(f"Unprocessed EMG data \n\n\n{emg_values}\n\n")   # For Debugging

    # Preprocessing EMG Data  
    emg_fs = 2148.148 # Sampling frequency of EMG sensor
    rectified_emg = np.abs(emg_values)
    emg_envelope = signal.savgol_filter(rectified_emg, window_length=int(0.2*emg_fs)|1, polyorder=3)

    print(f"Preprocessed EMG data:\n\tRectified EMG:\n\n{rectified_emg}\n\tEnvelope:\n\n{emg_envelope}\n\n")    # debug

    # Restrict to Reflex Window (t0 is the time at which the stretch reflex is induced)
    # Adjust t0 as needed to account for motor delay. Reflex is typically 15-50 ms after stretch
    emg_start = int(0 + 0.015 * emg_fs) 
    emg_end = int(0 + 0.050 * emg_fs)
    emg_segment = emg_envelope[emg_start:emg_end] # isolate the time window with only the reflex

    print(f"\n\n\tSegment:\n\n{emg_segment}")

    # EMG Peak Detection
    # .find_peaks returns (indices, properties). We just want the indices [0]
    emg_peaks = signal.find_peaks(
        emg_envelope, 
        prominence = 0.1*np.max(emg_envelope), 
        distance = int(0.2 * emg_fs), 
        width = int(0.005 * emg_fs), 
    )[0] # <--- Added [0] here to get only the array of indices

    print(f"\t\nPeak Indices:\n\n{emg_peaks}\n\n") # debug
    
    # EMG Max
    # Extract the values at those indices, then find the max
    # We use a 'if' check to avoid a crash if no peaks are found
    max_emg = np.max(emg_envelope[emg_peaks]) if len(emg_peaks) > 0 else 0

    print(f"\n\tMaxes:\n\n{max_emg}")

    # Converting force from a list to an np array
    force_data = np.array(force_data, dtype = float)

    # Preprocessing Force Data
    force_fs = 2148.148
    rectified_force = np.abs(force_data)
    force_envelope = signal.savgol_filter(force_data, window_length=int(0.2*force_fs)|1, polyorder = 3)

    print(f"Preprocessed EMG data:\n\tRectified EMG:\n\n{rectified_force}\n\tEnvelope:\n\n{force_envelope}\n\n")    # debug
    
    # Reflex Window for Force will start at EMG Window and last 2x
    force_start = emg_start
    force_end = 2*emg_end
    force_segment = force_envelope[force_start:force_end]

    print(f"\n\n\tSegment:\n\n{force_segment}")

    # Force Peak Detection
    # .find_peaks returns (indices, properties). We just want the indices [0]
    force_peaks = signal.find_peaks(
        force_envelope, 
        prominence = 0.1*np.max(force_envelope), 
        distance = int(0.2 * force_fs), 
        width = int(0.005 * force_fs), 
    )[0] # <--- Added [0] here to get only the array of indices

    print(f"\t\nPeak Indices:\n\n{force_peaks}\n\n") # debug
    
    # EMG Max
    # Extract the values at those indices, then find the max
    # We use a 'if' check to avoid a crash if no peaks are found
    max_emg = np.max(force_envelope[force_peaks]) if len(force_peaks) > 0 else 0

    print(f"\n\tMaxes:\n\n{max_emg}")

    # Threshold logic
    # is_success = True if max_emg < threshold
    is_success = max_emg < active_threshold if active_threshold > 0 else True
   
    return {
        "max_emg": max_emg,
        "max_force": max_force,
        "is_success": is_success
    }

def calculate_start_threshold(baseline_maxes):
    # takes the list of 50 baseline maxes, finds averaege and returns 65% of that
    if not baseline_maxes:
        return 0
    
    mean_max = sum(baseline_maxes) / len(baseline_maxes)
    threshold_65 = mean_max * 0.65

    return threshold_65

def threshold_adjust(session_success_list, current_threshold):
    # if 75% trial success rate, reduce current threshold by 35%
    if not session_success_list:
        return current_threshold
    
    total_trials = len(session_success_list)
    success_count = session_success_list.count(True)
    success_rate = success_count / total_trials

    if success_rate >= 0.75:
        new_threshold = current_threshold  * 0.65 # reduces by 35%
        return new_threshold
    
    return current_threshold