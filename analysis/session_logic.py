 # runs the loops and runs the motors for the ctypes

import time
import csv
import sys
import os
import threading
import ctypes
import pandas as pd
from analysis import processors
from toolbox import delsys_api_client as api
from toolbox.participant_manager import ParticipantDataManager
from itertools import zip_longest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

class SessionManager:
    def __init__(self, data_manager: ParticipantDataManager, gui_callback):
        """
        data_manager: ParticipantDataManager instance
        gui_callback: A function in the main GUI to update the plot/stats
        """
        self.lock = threading.Lock() # This should make each thread wait it's turn when making API calls

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
    
        print(f"##########################\n\nPair Status: {api.check_pair_status()}\n\n##########################")
        print(f"##########################\n\nReady to Steam: {api.ready_to_stream()}\n\n##########################")

        # # If statement for when we get the API working propperly and tested propperly
        # if(!api.check_pair_status())

        # else
        #     if(!api.ready_to_stream())


        """this works in parallel to the GUI via threading"""
        # collect data (where motor code and sensor code will live
        motor = ctypes.CDLL("/home/letrep/Downloads/Linux_Software/sFoundation/libMotor_working3.so")

        self.raw_force = []  # Clears the Force Data array before collection

        #initiate and home motors giving a 30000 ms window
        # motor.setup_and_home(30000)                     #allow motor to find home position
        motor.acceleration_velocity_set(1000,100)		#set a and v limits to 1000rpm/s and 500 rpm (medium movement)
        motor.move_counts(-8000,1)                      #move to 45 degrees
        time.sleep(1)                                   #wait for 2 seconds

        # PRE-TRIAL (e.g., Preloading Motors) may be included in base ctypes
        motor.acceleration_velocity_set(500, 30)        #set acceleration and velocity limits to 500rpm/s and 30rpm (slow movement)
        motor.move_speed(30)                            #move at 30 rpm                            
        time.sleep(.75)                                   #move for 1 second (check if it acts as a delay or pause)
        
        # Reflex induction and EMG Data Collection
        motor.acceleration_velocity_set(4000, 2000)      #set acceleration and velocity limits to 2000rpm/s and 500 rpm (quick movement)

        with self.lock:
            api.start_collect() # begins data collection for emg sensors
        self.ser.write(b'S')    # begins data collection for force        

        motor.move_counts(-1500, 1)                      #move to 500 counts offset from home
        time.sleep(2)                                    #changed from 0.5 to 2 just to see what happens
        self.ser.write(b'T') # stops force data collection
        self.raw_force = self._fetch_esp32_data()   # returns force data array from ESP32
        with self.lock:
            raw_emg = api.stop_collect()
        
        # This calls the bridge function below
        time.sleep(.5)                                   #wait for 1 seconds (temporarily waits for 2.5 seconds)
        # motor.shutdown_node()

        # ANALYSIS & SAVING
        results = processors.analize_trial(raw_emg, self.raw_force, self.active_threshold)
        self.session_maxes.append(results["max_emg"])
        self.success_history.append(results["is_success"])
        
        self._temp_save_and_move(
            self.p_id, self.entry_idx, self.sess_type, 
            self.current_trial_num, raw_emg, self.raw_force
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
            new_t = processors.calculate_start_threshold(self.session_maxes)

        else:
            # mastery check: if 75% success, reduce threshold by 35%
            new_t = processors.threshold_adjust(self.success_history, self.active_threshold)

        if new_t != self.active_threshold:
            self.dm.update_threshold(self.p_id, new_t)

    def _fetch_esp32_data(self):
        if not self.ser:
            return [0.0] * 100

        # 1. Clear any 'STARTED' or 'STOPPED' messages left over
        self.ser.reset_input_buffer()
        
        # 2. Trigger the dump
        self.ser.write(b'D')
        
        data = []
        # 3. Wait for the FIRST byte to arrive (up to 2 seconds)
        start_wait = time.time()
        while self.ser.in_waiting == 0:
            if (time.time() - start_wait) > 2.0:
                print("x ESP32 never started sending data.")
                return [0.0] * 100
            time.sleep(0.01)

        # 4. Now read until "END"
        while True:
            if self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if "END" in line:
                    break
                try:
                    data.append(float(line))
                except ValueError:
                    continue
            
            # Safety break if the stream just dies
            if (time.time() - start_wait) > 5.0: 
                break

        print(f"v Received {len(data)} force samples.")
        return data
    
    def _temp_save_and_move(self, p_id, entry_idx, sess_type, trial_num, emg, force):
        """
        Creates temp file so the participant manager can move it to its final home.
        """
        temp_name = f"temp_trial_{trial_num}.csv"
        with open(temp_name, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["EMG", "Force"])
            writer.writerows(zip_longest(emg, force, fillvalue=0))

        # Call existing "save_csv_to_session" from participant_manager.py
        self.dm.save_csv_to_session(p_id, entry_idx, sess_type, temp_name) # fix .dm to .pm

        if os.path.exists(temp_name):
            os.remove(temp_name)