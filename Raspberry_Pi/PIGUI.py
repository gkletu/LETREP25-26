#======================
# Main GUI - Raspberry Pi Version
#======================
import tkinter as tk
from tkinter import messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import sys
import subprocess
import os

# REMOVED: from win32inetcon import API_WRITE_DATA  # Windows-only library

#===========================
# Import function libraries
#===========================
from EMG_SpecAnn import select_and_load_csv
from participant_manager import ParticipantDataManager
from login_popup import ParticipantLoginPopup
#from Python import letrepEMGAPI as api
import session_manager as sm

#======================
# Import Theme
#======================
from theme import COLORS, FONTS

#======================
# Main app class
#======================
class ParticipantApp:
    """
    Only handles UI components and event handlers.
    Data management and processing are in separate modules.
    """

    def __init__(self, root):
        """Initializes main window"""
        self.root = root
        self.root.title('LETREP26 GUI')
        
        # Modified fullscreen for Raspberry Pi
        try:
            self.root.attributes('-fullscreen', True)
        except tk.TclError:
            # Fallback if fullscreen not supported
            self.root.attributes('-zoomed', True)
        
        self.root.configure(bg=COLORS['bg_main'])

        # Bind Escape key to exit fullscreen
        self.root.bind("<Escape>", lambda e: self._exit_fullscreen())

        # -------State variables-------
        self.current_participant = None
        self.current_entry_index = 0
        self.current_session = None
        self.current_csv_path = None

        #-------Initialize data manager-------
        self.data_manager = ParticipantDataManager()

        #--------Build UI components--------
        self._create_status_bar()
        self._create_button_frame()
        self._create_plot_frame()

        #--------Show login popup--------
        #self.root.after(100, self.Load_API)  #Launches API on start up

    def _exit_fullscreen(self):
        """Handle exiting fullscreen on Raspberry Pi"""
        try:
            self.root.attributes('-fullscreen', False)
        except tk.TclError:
            self.root.attributes('-zoomed', False)

    #=====================================
    # UI component creation
    #=====================================
    def _create_status_bar(self):
        """Creates status bar showing current participant/entry/session."""
        self.status_frame = tk.Frame(
            self.root,
            bg=COLORS['bg_frame'],
            relief=tk.SUNKEN,
            bd=2
        )
        self.status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = tk.Label(
            self.status_frame,
            text="No Participant Selected",
            font=FONTS['label_1'],
            bg=COLORS['bg_frame'],
            fg=COLORS['text_primary'],
            anchor='w'
        )
        self.status_label.pack(fill=tk.X, padx=5, pady=2)

    def _create_button_frame(self):
        """Create frame for main buttons with proper active colors and depressed look."""
        button_frame = tk.Frame(
            self.root,
            bg=COLORS['bg_raised'],
            relief=tk.RAISED,
            bd=2
        )
        button_frame.pack(padx=10, pady=10)

        # Start Session button (green, depressed initially)
        self.load_btn = tk.Button(
            button_frame,
            text="Start Session",
            font=FONTS['button'],
            bg=COLORS['success_active'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['success_active'],
            activeforeground=COLORS['text_primary'],
            command=self.Start_session,
            state=tk.DISABLED,
            width=15,
            height=2,
            relief=tk.SUNKEN
        )
        self.load_btn.grid(row=0, column=0, padx=10, pady=10)

        # Save Session button (blue, depressed initially)
        self.save_btn = tk.Button(
            button_frame,
            text="Save Session",
            font=FONTS['button'],
            bg=COLORS['blue_active'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['blue_active'],
            activeforeground=COLORS['text_primary'],
            command=self.save_to_session,
            state=tk.DISABLED,
            width=15,
            height=2,
            relief=tk.SUNKEN
        )
        self.save_btn.grid(row=0, column=1, padx=10, pady=10)

        # Change Participant button (always active)
        self.change_participant_btn = tk.Button(
            button_frame,
            text="Change Participant",
            font=FONTS['button'],
            bg=COLORS['purple_btn'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['purple_active'],
            activeforeground=COLORS['text_primary'],
            command=self.show_login_popup,
            width=18,
            height=2
        )
        self.change_participant_btn.grid(row=0, column=2, padx=10, pady=10)

        # Exit button (always active)
        self.exit_btn = tk.Button(
            button_frame,
            text='Exit',
            font=FONTS['button'],
            bg=COLORS['danger'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['danger_active'],
            activeforeground=COLORS['text_primary'],
            command=self.close_window,
            width=15,
            height=2
        )
        self.exit_btn.grid(row=0, column=3, padx=10, pady=10)

    def _create_plot_frame(self):
        """Create frame for displaying matplotlib plots."""
        self.plot_frame = tk.Frame(
            self.root,
            bg=COLORS['bg_frame'],
            relief=tk.SUNKEN,
            bd=2
        )
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    #===============================
    # Event Handlers
    #===============================
    def show_login_popup(self):
        """Shows login popup using ParticipantLoginPopup class."""
        popup = ParticipantLoginPopup(
            self.root, self.data_manager,
            on_success=self.on_login_success
        )

    def on_login_success(self, participant_id, entry_index, session):
        """Called when user successfully logs in and selects a session."""
        self.current_participant = participant_id
        self.current_entry_index = entry_index
        self.current_session = session

        self.update_status()

        # Enable buttons and switch to normal colors/RAISED relief
        self.load_btn.config(
            state=tk.NORMAL,
            bg=COLORS['success'],
            activebackground=COLORS['success_active'],
            relief=tk.RAISED
        )
        self.save_btn.config(
            state=tk.NORMAL,
            bg=COLORS['blue_btn'],
            activebackground=COLORS['blue_active'],
            relief=tk.RAISED
        )

        messagebox.showinfo(
            "Ready",
            f"Ready to work with Participant {participant_id}\n"
            f"Entry {entry_index + 1}, {session}"
        )

    def load_csv_file(self):
        """Open file dialog, load CSV, and display plot."""
        file_path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )

        if not file_path:
            return

        try:
            fig = select_and_load_csv(file_path)
            self.current_csv_path = file_path

            for widget in self.plot_frame.winfo_children():
                widget.destroy()

            canvas = FigureCanvasTkAgg(fig, self.plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            toolbar = NavigationToolbar2Tk(canvas, self.plot_frame)
            toolbar.update()

            # Enable save button if CSV is loaded
            self.save_btn.config(
                state=tk.NORMAL,
                bg=COLORS['blue_btn'],
                activebackground=COLORS['blue_active'],
                relief=tk.RAISED
            )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")

    def save_to_session(self):
        """Save current CSV to selected session folder."""
        if not self.current_csv_path:
            messagebox.showwarning("No Data", "Please load a CSV file first.")
            return

        success, result = self.data_manager.save_csv_to_session(
            self.current_participant,
            self.current_entry_index,
            self.current_session,
            self.current_csv_path
        )

        if success:
            messagebox.showinfo("Success", f"Data successfully saved to:\n{result}")
            self.save_btn.config(state=tk.DISABLED)
            self.current_csv_path = None
        else:
            messagebox.showerror("Error", f"Failed to save data to:\n{result}")

    def close_window(self):
        """Show exit confirmation popup."""
        popup = tk.Toplevel(self.root)
        popup.title("Confirm Exit")
        popup.geometry("450x250")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(bg=COLORS['bg_main'])

        tk.Label(
            popup,
            text="Are you sure you want to quit?",
            relief=tk.SUNKEN,
            borderwidth=2,
            font=FONTS['title'],
            bg=COLORS['bg_frame'],
            fg=COLORS['text_primary']
        ).pack(padx=10, pady=30, ipadx=5, ipady=5)

        button_frame = tk.Frame(
            popup,
            relief=tk.RAISED,
            borderwidth=2,
            bg=COLORS['bg_raised']
        )
        button_frame.pack(padx=10, pady=10)

        # Back button
        tk.Button(
            button_frame,
            text="Back",
            font=FONTS['button'],
            bg=COLORS['danger'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['danger_active'],
            activeforeground=COLORS['text_primary'],
            command=popup.destroy,
            width=10,
            height=2
        ).grid(row=0, column=0, padx=10, pady=5)

        # Quit button
        tk.Button(
            button_frame,
            text="Quit",
            font=FONTS['button'],
            bg=COLORS['success'],
            fg=COLORS['text_primary'],
            activebackground=COLORS['success_active'],
            activeforeground=COLORS['text_primary'],
            command=lambda: [self.root.destroy(), sys.exit()],
            width=10,
            height=2
        ).grid(row=0, column=1, padx=10, pady=5)

    def update_status(self):
        """Update status bar with current participant/entry/session info."""
        if self.current_participant and self.current_session:
            status_text = (
                f"Participant: {self.current_participant} | "
                f"Entry: {self.current_entry_index + 1} | "
                f"Session: {self.current_session}"
            )
        elif self.current_participant:
            status_text = f"Participant: {self.current_participant} | No session selected"
        else:
            status_text = "No participant selected"

        self.status_label.config(text=status_text)

    def Start_session(self):
        #session determined by current_session variable
        if not self.current_session:
            messagebox.showwarning("No Session Type Selected","Please Select A Session Type")
            return
        
        #list valid sessions
        valid_sessions = ["session1", "session2", "session3"]
        
        if self.current_session == "baseline":
            count = sm.baseline_motors(self.current_entry_index)
            messagebox.showinfo("Session Complete", f"Baseline loop ran {count} times")
        elif self.current_session in valid_sessions:
            count = sm.normal_motors(self.current_entry_index)
            messagebox.showinfo("Session Complete", f"Normal loop ran {count} times")
        else:
            messagebox.showerror("Error", f"Unknown session type: {self.current_session}")


#==========================================
# Main entry point
#==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = ParticipantApp(root)
    root.mainloop()