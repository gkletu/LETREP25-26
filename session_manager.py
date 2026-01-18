#Session manager: (template)
#   use session type to determine number of trials per session.

#==================
# Imports
#==================
import os
from datetime import datetime
import ctypes

# Import your API and ctype libraries
from Python import letrepEMGAPI as api

class SessionManager:
    """
    Session control logic:
        Motor control (ctypes)
        Force sensor activation (ctypes)
        EMG activation (API)
        Dataa collection coordination (potentially)
    """

def start_session(self, participant_id, entry_index, session):

    # determine if current is baseline session
    is_baseline = self._is_baseline_session(session)

    try:
        if is_baseline:
            return self._start_baseline_session(participant_id, entry_index, session)
        else:
            return self._start_normal_session(participant_id, entry_index, session)
    except Exception as e:
        return False, f"Error starting session: {e}" 

def _is_baseline_session(self, session):
    # Determining key word to determine if a session should be marked as baselin
    #EDIT LATER::::

def _start_baseline_session(self, participan_id, entry_index, session):
    # setup baseline save path for EMGs and force sensor

def _start_normal_session(self, participant_id, entry_index, session):
    # setup normal save path for EMGs and force sensor

def _baseline_motors(self, entry_index):
    # call ctype for motor control (50 trials)
    # call colection function
    
def _normal_motors(self, entry_index):
    # call ctype for motor control (75 trials)
    #call colection function