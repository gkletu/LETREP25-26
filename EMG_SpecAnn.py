import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os

def select_and_load_csv(file_path):
    """
    Loads a CSV file, performs FFT, filters, and returns a Matplotlib Figure.
    """

    # Get the file name for display
    file_name_Wex = os.path.basename(file_path)
    file_name = os.path.splitext(file_name_Wex)[0]

    # Load CSV (skip 2 header lines)
    df = pd.read_csv(file_path, skiprows=2, header=None)
    y = df.iloc[:, 0].values
    n = len(y)

    # Sampling setup
    sampling_rate = 2148.148  # Hz
    dt = 1 / sampling_rate
    t = np.arange(0, n * dt, dt)

    # FFT
    fhat = np.fft.fft(y, n)
    PSD = fhat * np.conj(fhat) / n
    freq = np.fft.fftfreq(n, d=dt)
    L = np.arange(1, int(np.floor(n / 2)))

    # Band-pass filter
    low_cut, high_cut = 20, 80
    band_mask = (np.abs(freq) >= low_cut) & (np.abs(freq) <= high_cut)
    fhat_filtered = fhat * band_mask
    y_filtered = np.fft.ifft(fhat_filtered)

    # --- Plot ---
    fig, axs = plt.subplots(3, 1, figsize=(10, 8))
    fig.suptitle(file_name)

    # Time domain
    axs[0].plot(t, y, label="Original", color="b")
    axs[0].set_title("Time Domain Signal")
    axs[0].set_xlabel("Time (s)")
    axs[0].set_ylabel("Amplitude (mV)")
    axs[0].legend()

    # Frequency domain
    axs[1].plot(freq[L], np.abs(PSD[L]), color="orange", label="Power Spectrum")
    axs[1].set_title("Frequency Domain")
    axs[1].set_xlabel("Frequency (Hz)")
    axs[1].set_ylabel("Magnitude")
    axs[1].set_xlim(0, sampling_rate / 2)
    axs[1].legend()

    # Filtered signal
    axs[2].plot(t, y_filtered.real, color="k", label="Filtered")
    axs[2].set_title("Filtered Signal (20–80 Hz)")
    axs[2].set_xlabel("Time (s)")
    axs[2].set_ylabel("Amplitude (mV)")
    axs[2].legend()

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_folder = os.path.join(current_dir, "Spec_Ann_PNGs")
    os.makedirs(save_folder, exist_ok = True)
    filepath = os.path.join(save_folder, f"{file_name}.png")

    plt.savefig(filepath, dpi = 300)

    return fig
