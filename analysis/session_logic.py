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
        """this works in parallel to the GUI via threading"""
        # collect data (where motor code and sensor code will live
        motor = ctypes.CDLL("/home/letrep/Downloads/Linux_Software/sFoundation/libMotor_working2.so")

        motor.setup()                                   
        #motor.acceleration_velocity_set(1000,500)		#slow down velocity
        #motor.move_counts(0,1)                          #ensure motor is at home
        #time.sleep(1.5)
        #motor.move_counts(-8000,1)                      #move to 45 deg

        # PRE-TRIAL (e.g., Preloading Motors) may be included in base ctypes
        #motor.move_speed(200) # move at 200 rpm
        #time.sleep(1)   # for 1 second

        # self.motor_library.move_to_start()
        #motor.acceleration_velocity_set(-8000, -500) #set acceleration to 8000 and velocity to 500
        motor.move_counts(0,1)							#extend to home position
        time.sleep(3)									#delay for 3/10 of a second

        #motor.shutdown_node()

        # DATA COLLECTION 
        # This calls the bridge function below
        raw_emg, raw_force = self._collect_data_samples()

        # ANALYSIS & SAVING
        results = analize_trial(raw_emg, raw_force, self.active_threshold)
        self.session_maxes.append(results['max_emg'])
        self.success_history.append(results['is_success'])
        
        self._temp_save_and_move(
            self.p_id, self.entry_idx, self.sess_type, 
            self.current_trial_num, raw_emg, raw_force
        )
        
        # UI UPDATE
        successes = self.success_history.count(True)
        fails = self.success_history.count(False)
        self.gui_update(self.session_maxes, self.active_threshold, successes, fails)

        if self.current_trial_num >= self.total_trials_needed:
            self._handle_end_of_session_math()
    
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
        # Placeholder for real sensor polling
        
        api.start_collect() # begins data collection for emg sensors
        duration = 2.0 # duration of emg collection in trial (seconds)
        time.sleep(duration) # wait for duration 

        emg_data = api.stop_collect() # returns the emg data from the trial as a dataframe
        
        force_data = []
        
        # Example Logic
        # duration = 2.0 # in seconds I think
        # start = time.time()
        # while (time.time() - start) < duration:
        #    force_data.append(self.serial_port.read())
        #    emg_data.append(self.socket.recv())
         
        return emg_data, [5.0, 5.5, 5.1] # (emg, force)
    
    def _temp_save_and_move(self, p_id, entry_idx, sess_type, trial_num, emg, force):
        """
        Creates temp file so the participant manager can move it to its final home.
        """
        temp_name = f"temp_trial_{trial_num}.csv"
        with open(temp_name, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["EMG", "Force"])
            writer.writerows(zip(emg, force))

        # Call existing "save_csv_to_session" from participant_manager.py
        self.dm.save_csv_to_session(p_id, entry_idx, sess_type, temp_name) # fix .dm to .pm

        if os.path.exists(temp_name):
            os.remove(temp_name)