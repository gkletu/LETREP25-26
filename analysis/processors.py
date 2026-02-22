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
    emg_values = emg_df['value'].tolist()

    # Preprocessing EMG Data  
    emg_fs = 2148.148 # Sampling frequency of EMG sensor
    rectified_emg = np.abs(emg_values)
    emg_envelope = scipy.signal.savgol_filter(rectified, window_length=int(0.2*emg_fs)|1, polyorder=3)

    # Restrict to Reflex Window (t0 is the time at which the stretch reflex is induced)
    # Adjust t0 as needed to account for motor delay. Reflex is typically 15-50 ms after stretch
    emg_start = int(t0 + 0.015 * emg_fs) 
    emg_end = int(t0 + 0.050 * emg_fs)
    emg_segment = envelope[start:end] # isolate the time window with only the reflex

    # EMG Peak Detection
    emg_peaks = find_peaks(
        emg_segment, # time window with only the reflex
        prominence = 0.1*np.max(emg_envelope), # peak must stand out by at least 10%
        distance = int(0.2 * emg_fs), # Ensures that peaks are at least 20 ms apart
        width = int(0.005 * emg_fs), # Requires peaks to be at  least 5 ms wide
    )
    
    # EMG Max
    max_emg = np.max(emg_peaks)

    # Preprocessing Force Data
    force_fs = 115200
    force_envelope = savgol_filter(force_signal, window_length=int(0.2*force_fs)|1, polyorder=3)

    # Restrict to Reflex Window
    force_start = int(t0 + 0.015*fs)  # 15 ms after stimulus
    force_end   = int(t0 + 0.050*fs)  # 50 ms after stimulus
    force_segment = force_envelope[start:end]

    # Force Peak Detection
    force_peaks = find_peaks(
    segment,
    prominence=0.05 * np.max(force_envelope),  # 5–10% of max force
    distance=int(0.02 * fs),                   # 20 ms minimal spacing
    width=int(0.005 * fs),                     # minimum 5 ms width
)

    # Force Max
    max_force = np.max(force_peaks)

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
    success_count = session_success_list(True)
    success_rate = success_count / total_trials

    if success_rate >= 0.75:
        new_threshold = current_threshold  * 0.65 # reduces by 35%
        return new_threshold
    
    return current_threshold