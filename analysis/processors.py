# processors.py 
# handles all the math, rectify, max, and threshold

import numpy as np
import pandas as pd
from scipy import signal

def analize_trial(emg_df, force_data, active_threshold=0):
    """
    Processes a single trial.
    emg_df: pandas DataFrame with ['value'] column
    force_data: list or numpy array (can be empty [])
    active_threshold: float (comparison for success)
    """
    # ==========================================
    # 1. EMG PROCESSING
    # ==========================================
    emg_fs = 2148.148 
    emg_values = emg_df['value'].values # Use .values for speed
    
    # Rectify and filter
    rectified_emg = np.abs(emg_values)
    # window_length must be odd. 0.2s * fs | 1 ensures it's odd.
    emg_envelope = signal.savgol_filter(rectified_emg, window_length=int(0.2*emg_fs)|1, polyorder=3)

    # Isolate Reflex Window (15ms to 50ms)
    emg_start = int(0.015 * emg_fs) 
    emg_end = int(0.050 * emg_fs)
    emg_segment = emg_envelope[emg_start:emg_end]

    # Peak Detection
    peaks, _ = signal.find_peaks(
        emg_segment,
        prominence=0.1 * np.max(emg_envelope) if len(emg_envelope) > 0 else 0,
        distance=int(0.02 * emg_fs),
        width=int(0.005 * emg_fs),
    )

    # Calculate max_emg from actual voltages at peak indices
    if len(peaks) > 0:
        max_emg = float(np.max(emg_segment[peaks]))
    else:
        max_emg = 0.0

    # ==========================================
    # 2. FORCE PROCESSING (Safe for Empty Arrays)
    # ==========================================
    max_force = 0.0
    
    if len(force_data) > 0:
        force_fs = 115200
        # Convert to numpy array just in case it's a list
        force_array = np.array(force_data)
        
        force_envelope = signal.savgol_filter(force_array, window_length=int(0.2*force_fs)|1, polyorder=3)

        force_start = int(0.015 * force_fs)
        force_end = int(0.050 * force_fs)
        
        # Ensure we don't slice out of bounds
        if len(force_envelope) > force_end:
            force_segment = force_envelope[force_start:force_end]
            f_peaks, _ = signal.find_peaks(
                force_segment,
                prominence=0.05 * np.max(force_envelope),
                distance=int(0.02 * force_fs),
                width=int(0.005 * force_fs),
            )
            if len(f_peaks) > 0:
                max_force = float(np.max(force_segment[f_peaks]))

    # ==========================================
    # 3. SUCCESS LOGIC & RETURN
    # ==========================================
    # is_success is True if max_emg is strictly less than threshold
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