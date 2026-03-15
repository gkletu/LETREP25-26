 # session_logic.py
 # runs the loops and runs the motors for the ctypes

import time
import csv
import sys
import os
import threading
import ctypes
import pandas as pd

from analysis import processors
# from processors import analize_trial, calculate_start_threshold, threshold_adjust  #IDK what this is for, theyre in the same folder, I shouldnt need this...
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
from toolbox import delsys_api_client as api
from toolbox.participant_manager import ParticipantDataManager

# collect data (where motor code and sensor code will live
motor = ctypes.CDLL("/home/letrep/Downloads/Linux_Software/sFoundation/libMotor_working3.so")

class SessionManager:
    def __init__(self, data_manager: ParticipantDataManager, gui_callback):
        """
        data_manager: ParticipantDataManager instance
        gui_callback: A function in the main GUI to update the plot/stats
        """
        self.dm = data_manager   #use instance passed from the GUI
        self.gui_update = gui_callback

        # state variables for current active entry
        self.active_threshold = 0.0
        self.session_maxes = []
        self.success_history = []
        self.current_trial_num = 0
        self.total_trials_needed = 0
        self.p_id = None
        self.entry_idx = None
        self.sess_type = None

    def prepare_session(self, p_id, entry_idx, session_type):
        """Sets up the session variables but doesn't run the loop"""
        self.p_id = p_id
        self.entry_idx = entry_idx
        self.sess_type = session_type

        # Load threshold (if there is one saved)
        try:
            self.active_threshold = self.dm.get_threshold(p_id)
        except AttributeError:
            self.active_threshold = 0.0 # fallback if no threshold

        self.session_maxes = []
        self.success_history = []
        self.current_trial_num = 0
        self.total_trials_needed = 50 if session_type == "baseline" else 75
        return self.total_trials_needed

    def run_single_trial(self):
        """Runs one trial, updates GUI and returns True if more trials remain"""
        if self.current_trial_num >= self.total_trials_needed:
            return False
        
        self.current_trial_num += 1

        threading.Thread(target=self._trial_worker, daemon=True).start()
        
        return True
    
    def _trial_worker(self):
        """Runs in parallel to the GUI. Executes motor sequence, saves data, and triggers next trial."""
        try:
            # 1. INITIAL MOVEMENT: Move to 45 degrees
            motor.acceleration_velocity_set(2000, 50)
            motor.move_counts(-8000, 1)                      
            time.sleep(2)                                   

            # 2. PRE-TRIAL: Slow pre-load movement
            motor.acceleration_velocity_set(8000, 30)        
            motor.move_speed(30)                            
            time.sleep(0.5)                                   

            # 3. REFLEX INDUCTION: Fast quick movement
            motor.acceleration_velocity_set(8000, 1000)      
            motor.move_counts(-1000, 1)                      
            
            # 4. DATA COLLECTION: Collect 2.0s of data during/after reflex
            raw_emg, raw_force = self._collect_data_samples()          
            time.sleep(3) # Wait for motor to finish and system to settle

            # 5. ANALYSIS & SAVING
            results = processors.analize_trial(raw_emg, raw_force, self.active_threshold)
            self.session_maxes.append(results['max_emg'])
            self.success_history.append(results['is_success'])
            
            self._temp_save_and_move(
                self.p_id, self.entry_idx, self.sess_type, 
                self.current_trial_num, raw_emg, raw_force
            )
            
            # 6. UI UPDATE
            successes = self.success_history.count(True)
            fails = self.success_history.count(False)
            self.gui_update(self.session_maxes, self.active_threshold, successes, fails)

            # 7. MOTOR RESET: Return to start position so next trial is accurate
            # We move +9000 to offset the -8000 and -1000 moves above
            motor.acceleration_velocity_set(2000, 50)
            motor.move_counts(9000, 1) 
            time.sleep(1)

            # 8. THE LOOP LOGIC: Check if we need more trials
            if self.current_trial_num >= self.total_trials_needed:
                # End of session math (calculates new threshold)
                self._handle_end_of_session_math()
                print(f"Session Complete: {self.total_trials_needed} trials recorded.")
            else:
                # INTER-TRIAL INTERVAL: 5-second rest for participant
                time.sleep(4) 
                
                # BATON PASS: Tell the main GUI thread to start the next trial
                # We use root.after because we can't start a new thread FROM this thread safely
                self.dm.root.after(100, self.run_single_trial)

        except Exception as e:
            print(f"Critical error in trial {self.current_trial_num}: {e}")
            # Optionally call a GUI error handler here
    
    def _handle_end_of_session_math(self):
        """
        Calculates and saves new thresholds based on performance.
        """
        if self.sess_type == "baseline":
            new_t = calculate_start_threshold(self.session_maxes)

        else:
            # mastery check: if 75% success, reduce threshold by 35%
            new_t = threshold_adjust(self.success_history, self.active_threshold)

        if new_t != self.active_threshold:
            self.dm.update_threshold(self.p_id, new_t)


    def _collect_data_samples(self):
        """Begins data collection for sensors and returns the datasets."""
        api.start_collect() 
        duration = 2.0 
        time.sleep(duration) 

        # This returns a DataFrame with columns: samples, time, value
        emg_data = api.stop_collect() 
        
        # Placeholder for force data as an empty list
        force_data = [] 
         
        return emg_data, force_data

    def _temp_save_and_move(self, p_id, entry_idx, sess_type, trial_num, emg_df, force):
        """
        Saves the DataFrame to a CSV without losing data rows, 
        then moves it to the permanent participant folder.
        """
        temp_name = f"temp_trial_{trial_num}.csv"

        # If force is empty, we add a placeholder column to the DataFrame 
        # so the CSV structure remains consistent for future analysis.
        if not force:
            emg_df['force_placeholder'] = 0.0
        else:
            # If you eventually have force data, you'd handle length matching here.
            # For now, we ensure the EMG data is preserved entirely.
            pass

        # Save the entire DataFrame to CSV
        emg_df.to_csv(temp_name, index=False)

        # Use the data manager to move the file to the correct participant directory
        self.dm.save_csv_to_session(p_id, entry_idx, sess_type, temp_name)

        # Cleanup the temporary file
        if os.path.exists(temp_name):
            os.remove(temp_name)