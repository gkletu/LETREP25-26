# handles all the math, rectify, max, and threshold
import os
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal
from scipy import stats


def analize_trial(emg_df, force_df, active_threshold=0):
    # Processes a single trial
    # emg_data: raw EMG dataframe
    # force_data: raw force data
    # active_threshold: 65% the baseline average for comparison

    # Extract list of EMG magnitude from EMG dataframe
    emg_values = emg_df["value"].to_numpy(dtype = float)
    emg_values = emg_values / 909  # Convert Volts to Millivolts (removes the amplifier (x909)) (changed from * 1000)

    emg_timestamps = emg_df['time'].to_numpy(dtype = float)
    emg_timestamps = emg_timestamps * 1000  # Converts seconds to ms
    
    print(f"\n\nEmg Values length: {emg_values.size}\n\n")
    # Preprocessing EMG Data  
    emg_fs = 2148.148 # Sampling frequency of EMG sensor
    rectified_emg = np.abs(emg_values)
    emg_envelope = signal.savgol_filter(rectified_emg, window_length=int(0.2*emg_fs)|1, polyorder=3)

    # print(f"Preprocessed EMG data:\n\tRectified EMG:\n\n{rectified_emg}\n\tEnvelope:\n\n{emg_envelope}\n\n")    # debug

    # Restrict to Reflex Window (t0 is the time at which the stretch reflex is induced)
    # Adjust t0 as needed to account for motor delay. Reflex is typically 15-50 ms after stretch
    emg_start = int(0 + 0.015 * emg_fs) 
    emg_end = int(0 + 0.050 * emg_fs)
    emg_segment = emg_envelope[emg_start:emg_end] # isolate the time window with only the reflex

    # EMG Peak Detection
    # .find_peaks returns (indices, properties). We just want the indices [0]
    emg_peaks = signal.find_peaks(
        emg_envelope, 
        prominence = 0.1*np.max(emg_envelope), 
        distance = int(0.2 * emg_fs), 
        width = int(0.005 * emg_fs), 
    )[0] # <--- Added [0] here to get only the array of indices
    
    # EMG Max
    # Extract the values at those indices, then find the max
    # We use a 'if' check to avoid a crash if no peaks are found
    max_emg = np.max(emg_envelope[emg_peaks]) if len(emg_peaks) > 0 else 0

    # print(f"\n\tMaxes:\n\n{max_emg}")

    # Converting force from a list to an np array
    force_values = force_df['force_V'].to_numpy(dtype = float)
    force_values = force_values * 1.8 / 51  # Converting volts to Newtons 1.8V/N sensitivity and removing instrumentation amp gain of 51

    force_timestamps = force_df['timestamp_us'].to_numpy(dtype = float)
    force_timestamps = force_timestamps / 1000  # Convering timestamps from microseconds to milliseconds

    # Preprocessing Force Data
    force_fs = 2148
    rectified_force = np.abs(force_values)
    force_envelope = signal.savgol_filter(rectified_force, window_length=int(0.1*force_fs)|1, polyorder = 3)
    
    # Reflex Window for Force will start at EMG Window and last 2x
    force_start = emg_start
    force_end = emg_end
    force_segment = force_envelope[force_start:force_end]

    # Force Peak Detection
    # .find_peaks returns (indices, properties). We just want the indices [0]
    force_peaks = signal.find_peaks(
        rectified_force, 
        prominence = 0.1*np.max(rectified_force), 
        distance = int(0.2 * force_fs), 
        width = int(0.005 * force_fs), 
    )[0] # <--- Added [0] here to get only the array of indices
    
    # EMG Max
    # Extract the values at those indices, then find the max
    # We use a 'if' check to avoid a crash if no peaks are found
    max_force = np.max(rectified_force[force_peaks]) if len(force_peaks) > 0 else 0

    # Threshold logic
    # is_success = True if max_emg < threshold
    is_success = max_emg < active_threshold if active_threshold > 0 else True

    _debug_plot(emg_timestamps, emg_values, rectified_emg, emg_envelope, emg_peaks, force_timestamps, force_values, rectified_force, force_envelope, force_peaks)
   
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

def _debug_plot(emg_time, raw_emg, rectified_emg, emg_envelope, emg_peaks, force_time, raw_force, rectified_force, force_envelope, force_peaks):
    fig, axs = plt.subplots(2, 4, figsize =(18,10))
    fig.suptitle('Comprehensive Trial, Analysis', fontsize = 16, fontweight = 'bold')

    # Column 0 Raw Data
    axs[0, 0].plot(emg_time, raw_emg, color = 'blue')
    axs[0, 0].set_title('Raw EMG')
    axs[0, 0].set_ylabel('mV')
    axs[0, 0].set_xlabel('ms')

    axs[1, 0].plot(force_time, raw_force, color = 'red')
    axs[1, 0].set_title("Raw Force")
    axs[1, 0].set_ylabel("N")
    axs[1, 0].set_xlabel("ms")

    # Column 1: Envelopes
    axs[0, 1].plot(emg_time, emg_envelope, color = 'blue')
    axs[0, 1].set_title('EMG Envelope')
    axs[0, 1].set_ylabel('mV')
    axs[0, 1].set_xlabel('ms')

    axs[1, 1].plot(force_time, force_envelope, color = 'red')
    axs[1, 1].set_title("Force Envelope")
    axs[1, 1].set_ylabel("N")
    axs[1, 1].set_xlabel("ms")

    # Column 2: Overlays
    # Raw overlay (EMG and Force)
    ax_emg_raw = axs[0, 2]
    ax_force_raw = ax_emg_raw.twinx()
    ax_emg_raw.plot(emg_time, raw_emg, color='blue', alpha=0.5, label='EMG')
    ax_force_raw.plot(force_time, raw_force, color='red', alpha=0.5, label='Force')
    ax_emg_raw.set_title('Raw Overlay')

    # Envelope/Peak overlay
    ax_emg_env = axs[1, 2]
    ax_force_env = ax_emg_env.twinx()
    ax_emg_env.plot(emg_time, emg_envelope, color='darkblue', alpha=0.7)
    ax_force_env.plot(force_time, raw_force, color='red', alpha=0.3)
    
    if len(emg_peaks) > 0:
        ax_emg_env.plot(emg_time[emg_peaks], emg_envelope[emg_peaks], 'bx', markersize=8)
    
    if len(force_peaks) > 0:
        ax_force_env.plot(force_time[force_peaks], raw_force[force_peaks], 'rx', markersize=8)
    
    ax_emg_env.set_title('EMG Env & Force Peak Overlay')

    # Column 3: Phase plot with linear trend line and R^2 annotation
    min_length = min(len(emg_envelope), len(raw_force))
    if min_length > 0:
        # Interpolate EMG Envelope to match Force time Stamps
        emg_aligned = np.interp(force_time, emg_time, emg_envelope)

        # Prepare x and y for plotting/regression
        x = raw_force
        y = emg_aligned

        # Scatter/line plot of phase relationship
        axs[0, 3].plot(x, y, color = 'purple', alpha = 0.6, label = 'EMG vs Force')

        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        trend_line = slope * x + intercept

        # Overlay trend line
        axs[0, 3].plot(x, trend_line, color='orange', linestyle='--', linewidth=2, label='Trend Line')
        
        # Add equation and R² as text annotation
        eq_text = f"y = {slope:.3f}x + {intercept:.3f}\n$R^2$ = {r_value**2:.3f}"
        axs[0, 3].text(0.05, 0.95, eq_text, transform=axs[0, 3].transAxes,
                    fontsize=10, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.6))
        
        # Labels and title
        axs[0, 3].set_xlabel('Raw Force (N)')
        axs[0, 3].set_ylabel('EMG Env (mV)')
        axs[0, 3].set_title('Phase Plot')
        axs[0, 3].legend()
    
    axs[1, 3].axis('off')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # Replace plt.show() with a save command
    if not os.path.exists('debug_plots'):
        os.makedirs('debug_plots')
    
    # Save with a timestamp or trial ID to avoid overwriting
    plt.savefig(f"debug_plots/trial_{int(time.time())}.png")
    plt.close(fig) # Critical: close the figure to free up memory