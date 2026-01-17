# ======================
# Session Manager  !!TEMPLATE!!
# ======================
import os
from datetime import datetime


class SessionManager:
    """
    Handles session startup logic including:
    - File path generation
    - Motor configuration
    - Display configuration
    """

    def __init__(self, data_manager):
        """Initialize with reference to data manager."""
        self.data_manager = data_manager
        self.save_path = None
        self.current_config = None

    def setup_save_path(self, participant_id, entry_index, session):
        """Create save path and filename based on participant ID and session."""
        base_path = self.data_manager.get_participant_folder(participant_id)
        session_folder = os.path.join(base_path, session)

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Entry_{entry_index + 1}_{session}_{timestamp}.csv"

        self.save_path = os.path.join(session_folder, filename)

        # Ensure directory exists
        os.makedirs(session_folder, exist_ok=True)

        return self.save_path

    def get_motor_config(self, entry_index):
        """Return motor configuration based on entry type."""
        motor_configs = {
            0: "CONFIG_1",  # Entry 1
            1: "CONFIG_2",  # Entry 2
            2: "CONFIG_3",  # Entry 3
            # Add more as needed
        }

        config = motor_configs.get(entry_index, "DEFAULT_CONFIG")
        self.current_config = config
        return config

    def get_display_info(self, entry_index):
        """Return display information based on entry type."""
        display_info = {
            0: {
                'title': "Entry 1: Baseline Assessment",
                'instructions': "Instructions for entry 1...",
                'color': '#00FF00'
            },
            1: {
                'title': "Entry 2: Active Testing",
                'instructions': "Instructions for entry 2...",
                'color': '#0000FF'
            },
            2: {
                'title': "Entry 3: Recovery Phase",
                'instructions': "Instructions for entry 3...",
                'color': '#FF00FF'
            },
            # Add more as needed
        }

        return display_info.get(entry_index, {
            'title': "Unknown Entry Type",
            'instructions': "No instructions available",
            'color': '#FFFFFF'
        })

    def send_motor_command(self, config):
        """Send command to motor API."""
        # TODO: Implement based on your API communication method
        # Examples:
        # - Write to a file that the API reads
        # - Send via socket
        # - Use subprocess to call API command
        # - etc.

        print(f"Sending motor configuration: {config}")
        # Placeholder for actual implementation
        pass