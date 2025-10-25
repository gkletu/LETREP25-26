import tkinter as tk
from tkinter import ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from EMG_SpecAnn import select_and_load_csv

def button_click():
    # Open file dialog
    file_path = filedialog.askopenfilename(
        title="Select CSV file", filetypes=[("CSV Files", "*.csv")]
    )

    if not file_path:
        print("No file selected.")
        return

    # Create the figure from the analysis function
    fig = select_and_load_csv(file_path)

    # Embed the figure in the Tkinter window
    for widget in frame.winfo_children():
        widget.destroy()  # Clear any previous plots

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    toolbar = NavigationToolbar2Tk(canvas, frame)
    toolbar.update()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


# --- MAIN WINDOW ---
MainWindow = tk.Tk()
MainWindow.title("LETREP 26 1.0")
MainWindow.attributes("-fullscreen", True)
MainWindow.bind("<Escape>", lambda e: MainWindow.attributes('-fullscreen', False))
MainWindow.geometry("850x750")
MainWindow.configure(bg="#857C6D")

# Title label
Main_label = ttk.Label(MainWindow, text="LETREP 26", font=("calibri", 24),
                       background="#857C6D", foreground="#38D65C")
Main_label.pack(padx=10, pady=10)

# Button
btn1 = tk.Button(MainWindow, text="Filter", background="#38B56C",
                 activebackground="#38A65C", command=button_click)
btn1.pack(padx=10, pady=10)

# Frame for the plot
frame = tk.Frame(MainWindow, bg="#857C6D")
frame.pack(fill=tk.BOTH, expand=True)

# Run the app
MainWindow.mainloop()