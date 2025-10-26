import tkinter as tk
from tkinter import ttk, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from EMG_SpecAnn import select_and_load_csv

def close_window():
    # Create popup window
    popup = tk.Toplevel()
    popup.title("Confirm Exit")
    popup.geometry("450x200")
    popup.resizable(False,False)
    popup.grab_set() # Makes popup modal and disables interaction with MainWindow
    popup.configure(bg = "#857C6D")

    Plabel = tk.Label(popup, text = "Are you sure you want to quit?", font = ("calibri", 24), bg = "#857C6D")
    Plabel.pack(padx = 10, pady = 10)

    Pbutton_frame = tk.Frame(popup, bg = "#756E60")
    Pbutton_frame.pack(pady = 5)

    def on_Quit():
        MainWindow.destroy()

    def on_Back():
        popup.destroy()

    Pbtn1 = tk.Button(Pbutton_frame, text = "QUIT", background = "#B00707", activebackground = "#9C0606", command = on_Quit)
    Pbtn1.grid(row = 0, column = 1, padx = 5, pady = 5, ipadx = 20, ipady = 20)

    Pbtn2 = tk.Button(Pbutton_frame, text = "BACK", background = "#38B56C", activebackground = "#38A65C", command = on_Back)
    Pbtn2.grid(row = 0, column = 0, padx = 5, pady = 5, ipadx = 20, ipady = 20)

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
Main_label = ttk.Label(MainWindow, text="LETREP 26", font=("calibri", 24), background="#857C6D", foreground="#38D65C")
Main_label.pack(padx = 10, pady = 10)

# Button
style = ttk.Style()
style.theme_use("clam")
style.configure("colored.TFrame", background="#756E60")

button_frame = ttk.Frame(MainWindow, style = "colored.TFrame")
button_frame.pack(padx = 10, pady = 10)

btn1 = tk.Button(button_frame, text="Filter", background="#38B56C", activebackground="#38A65C", command=button_click)
btn1.grid(row = 0, column = 0, padx = 10, pady = 10, ipadx = 20, ipady = 20)

btn2 = tk.Button(button_frame, text = "EXIT", background = "#B00707", activebackground = "#9C0606", command = close_window)
btn2.grid(row = 0, column = 1, padx = 10, pady = 10, ipadx = 20, ipady = 20)

# Frame for the plot
frame = tk.Frame(MainWindow, bg="#756E60")
frame.pack(fill=tk.BOTH, expand=True)

# Run the app
MainWindow.mainloop()