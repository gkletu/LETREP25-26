# runs the loops and runs the motors for the ctypes

import time
import csv
import sys
import os
import threading
from analysis.processors import analyze_trial, calculate_start_threshold, threshold_adjust
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))
from toolbox.participant_manager import ParticipantDataManager

class SessionManager:
    def __init__(self, data_manager, gui_callback):
        """
        data_manager: ParticipantDataManager instance
        gui_callback: A function in the main GUI to update the plot/stats
        """
        self.dm = ParticipantDataManager
        self.gui_update = gui_callback

        # state variables for current active entry
        self.active_threshold = 0.0
        self.session_maxes = []
        self.success_history = []

    def run_entry(self, p_id, entry_idx, session_type):
        """
        Main execution loop for an entry.
        Determines trial count and handles the threshold management.
        """
        # Load existing threshold from JSON log
        self.active_threshold = self.dm.get_threshold(p_id)

        # reset entry states
        self.session_maxes = []
        self.success_history = []
        num_trials = 50 if session_type == "baseline" else 75

        for i in range(num_trials):
            trial_num = i + 1

            # Hardware Interaction
              #this is where ctypes are called
            raw_emg, raw_force = self._collect_data_samples()

            # Analysis 
            results = analyze_trial(raw_emg, raw_force, self.active_threshold)
            
            # Update local history
            self.session_maxes.append(results['max_emg'])
            self.success_history.append(results['is_success'])

            # save raw csv via data manager
            self._temp_save_and_move(p_id, entry_idx, session_type, trial_num, raw_emg, raw_force)

            # Update the GUI plot and counters (not sure if the false works yet...)
            self.gui_update(self.session_maxes, self.success_history.count(True), self.success_history.count(False))

        # Post-session threshold logic
        self._handle_end_of_session_math(p_id, session_type)

        return self.session_maxes
    
    def _handle_end_of_session_math(self, p_id, session_type):
        """
        Calculates and saves new thresholds based on performance.
        """
        if session_type == "baseline":
            # initial setup: 65% of average of 50 trials
            new_t = calculate_start_threshold(self.session_maxes)
            self.dm.update_threshold(p_id, new_t) #Issues with update_threshold
            self.active_threshold = new_t
            print(f"Baseline Complete. threshold set to: {new_t}")

        elif session_type in ["entry1", "entry2", "entry3"]:
            # mastery check: if 75% success, reduce threshold by 35%
            new_t = threshold_adjust(self.success_history, self.active_threshold)

            if new_t != self.active_threshold:
                self.dm.updata_threshold(p_id, new_t)
                self.active_threshold = new_t
                print(f"Mastery Achieved! New Threshold: {new_t}")

    def _collect_data_samples(self):
        # Placeholder for real sensor polling
        time.sleep(0.1) # simulate hardware delay
        return [0.5, 0.6, 0.4], [10, 12, 11] # EMG, Force
    
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