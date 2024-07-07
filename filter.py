import numpy as np
import scipy.signal
import scipy.io.wavfile
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

def lowpass(data: np.ndarray, cutoff: float, sample_rate: float, poles: int = 5):
    sos = scipy.signal.butter(poles, cutoff, 'lowpass', fs=sample_rate, output='sos')
    filtered_data = scipy.signal.sosfiltfilt(sos, data)
    return filtered_data

def highpass(data: np.ndarray, cutoff: float, sample_rate: float, poles: int = 5):
    sos = scipy.signal.butter(poles, cutoff, 'highpass', fs=sample_rate, output='sos')
    filtered_data = scipy.signal.sosfiltfilt(sos, data)
    return filtered_data

def bandpass(data: np.ndarray, edges: list[float], sample_rate: float, poles: int = 5):
    sos = scipy.signal.butter(poles, edges, 'bandpass', fs=sample_rate, output='sos')
    filtered_data = scipy.signal.sosfiltfilt(sos, data)
    return filtered_data

# Load sample data from a WAV file
sample_rate, data = scipy.io.wavfile.read('sample411.wav')
times = np.arange(len(data))/sample_rate
print(times)

# Apply a 50 Hz low-pass filter to the original data
filtered = lowpass(data, 15, sample_rate)

# # Apply a 20 Hz high-pass filter to the original data
# filtered = highpass(data, 15, sample_rate)

# # Apply a 10-50 Hz high-pass filter to the original data
# filtered = bandpass(data, [10, 50], sample_rate)

print(filtered)

peakArray, _ = find_peaks(filtered, sample_rate)
print(peakArray)
totalBeat = peakArray.shape[0]
print(totalBeat)


# Code used to display the result
fig, (ax1, ax2) = plt.subplots(2,1, figsize=(10, 3), sharex=True, sharey=True)
ax1.plot(times, data)
ax1.set_title("Original Signal")
ax1.margins(0, .1)
ax1.grid(alpha=.5, ls='--')
ax2.plot(times, filtered)
# Add X markers at the peak locations
# ax2.plot(times[peakArray], filtered[peakArray], "x", linestyle='', color='r', markersize=8, label='Peaks')
ax2.set_title("Low Pass Filter (15Hz)")
ax2.grid(alpha=.5, ls='--')
plt.tight_layout()
plt.show()