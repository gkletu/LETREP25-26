# handles all the math, rectify, max, and threshold

import numpy as np

def analyze_trial(emg_data, force_data, active_threshold=0):
    # Processes a single trial
    # emg_data: raw EMG data
    # force_data: raw force data
    # active_threshold: 65% the baseline average for comparison

    # Rectify and find EMG max
    rectified_emg = [abs(x) for x in emg_data]
    max_emg = max(rectified_emg) if rectified_emg else 0

    # Find max force
    max_force = max(force_data) if force_data else 0

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