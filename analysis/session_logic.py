# runs the loops and runs the motors for the ctypes

import time
import csv
import os
import threading
from analysis.processors import analyze_trial, calculate_start_threshold, threshold_adjust

class SessionManager:
    def __init__(self, data_manager, gui_callback):
        """
        data_manager: ParticipantDataManager instance
        gui_callback: A function in the main GUI to update the plot/stats
        """
        self.dm: data_manager