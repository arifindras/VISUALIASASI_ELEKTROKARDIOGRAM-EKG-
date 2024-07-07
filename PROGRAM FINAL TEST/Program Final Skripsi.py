#BOT serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pandas as pd
# import random
import time
import scipy.signal
from scipy.io.wavfile import write
from scipy.signal import find_peaks
import requests
import serial
import serial.tools.list_ports

TOKEN = "6945383482:AAGtACEB30LcvqUbIYMsAt5cFBcQLVUyDIQ" #token id bot telegram
CHAT_ID = "6163399679" #pasword id bot telegram

uplinkInterval = 60
samplingDuration = 10 #dalam detik
samplingRate = 100 #sample per detik
threshold = 0.7 #menentukan peak
samplingTotal = samplingRate*samplingDuration #jumlah data sample per menit
yLimit1 = [400,900] #limit nilai ADC
yLimit2 = [-150,230] #limit nilai ADC
yLimit3 = [-150,900] #limit nilai ADC
timeSpace = samplingDuration/samplingTotal
timeLabel = np.arange(0, samplingDuration, timeSpace)
rawDataArray = np.zeros(samplingTotal)
filteredDataArray = np.zeros(samplingTotal)
peakArray = np.array([])
timeLabelPeak = np.array([])
peakValue = np.array([])
totalBeatArray = np.zeros(10)

bpm = 0
nama = usia = gender = "" #data diri peserta

# Membuat grafik dengan subplot
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15))  # tiga subplot
# Menambahkan penyesuaian ruang antara subplot
plt.subplots_adjust(hspace=0.5)

ax1.set_ylim(yLimit1)
ax1.set_title("RAW Data") # Mengatur judul plot
ax1.set_ylabel("ADC") # Mengatur label sumbu y
ax1.set_xlabel("Time") # Mengatur label sumbu x

ax2.set_ylim(yLimit2)
ax2.set_title("Filtered Data") # Mengatur judul plot
ax2.set_ylabel("ADC") # Mengatur label sumbu y
ax2.set_xlabel("Time") # Mengatur label sumbu x

ax3.set_ylim(yLimit3)
ax3.set_title("Combined Data") # Mengatur judul plot
ax3.set_ylabel("ADC") # Mengatur label sumbu y
ax3.set_xlabel("Time") # Mengatur label sumbu x

# Gunakan gaya garis yang sama seperti yang digunakan sebelumnya
line1, = ax1.plot(timeLabel, rawDataArray, 'r', animated=True)
line2, = ax2.plot(timeLabel, filteredDataArray, 'b', animated=True)
line5, = ax2.plot(timeLabelPeak, peakValue, "x", linestyle='', color='g', markersize=8, label='Peaks')
line3, = ax3.plot(timeLabel, rawDataArray, 'r', animated=True)
line4, = ax3.plot(timeLabel, filteredDataArray, 'b', animated=True)

# Inisialisasi teks BPM
bpmText = ax3.text(0.99, 0.965, "", fontsize=12, verticalalignment='top', horizontalalignment='right', transform=ax3.transAxes, bbox=dict(facecolor='white', alpha=0.5))

# Kirim gambar ke BOT
def sendData(caption):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    # Buka file gambar lokal dalam mode binary (rb)
    with open("chartResult.png", "rb") as file:
        files = {"photo": file}
        # Menyertakan caption message dalam data
        data = {
            "chat_id": CHAT_ID,  # ID grup atau pengguna
            "caption": caption  # Pesan teks yang ingin dikirim sebagai caption
        }
        # Mengirim permintaan POST ke API Telegram dengan menggunakan requests
        response = requests.post(url, data=data, files=files)

    # Mengecek jika permintaan berhasil
    if response.status_code == 200:
        print("Data berhasil dikirim!") #keterangan pengiriman 
    else:
        print("Gagal mengirim data.") #keterangan pengiriman

def calculateBPM(dataArray):
    global threshold, totalBeatArray

    minTh = dataArray.min()
    # if minTh < 400 : minTh = 400
    maxTh = dataArray.max()

    # ax1.set_ylim(minTh, maxTh)
    # ax2.set_ylim(minTh, maxTh)
    # ax3.set_ylim(minTh, maxTh)

    # ax1.yaxis.get_major_locator().set_params(nbins=5)  # Anda dapat mengubah nilai nbins sesuai kebutuhan
    # ax2.yaxis.get_major_locator().set_params(nbins=5)
    # ax3.yaxis.get_major_locator().set_params(nbins=5)

    #threshold dinamis 80%
    peakThreshol = minTh + (maxTh - minTh)*threshold
    # Deteksi Puncak
    peakArray, _ = find_peaks(dataArray, peakThreshol)

    #update grafik peaks
    timeLabelPeak = timeLabel[peakArray]
    peakValue = filteredDataArray[peakArray]
    line5.set_xdata(timeLabelPeak)
    line5.set_ydata(peakValue)

    # Menghitung jumlah puncak/denyut
    totalBeat = len(peakArray)*(60/samplingDuration)

    # Moving Average Filter BPM
    totalBeatArray = totalBeatArray[1:]
    totalBeatArray = np.append(totalBeatArray, totalBeat)
    avgTotalBeat = int(totalBeatArray.mean())

    return avgTotalBeat

# def updateYlimit():
#     minThRaw = rawDataArray.min()
#     maxThRaw = rawDataArray.max()
#     minThFiltered = filteredDataArray.min()
#     maxThFiltered = filteredDataArray.max()

#     ax1.set_ylim(minThRaw, maxThRaw)
#     ax2.set_ylim(minThFiltered, maxThFiltered)
#     ax3.set_ylim(minThFiltered, maxThRaw)

#     ax1.yaxis.get_major_locator().set_params(nbins=5)  # Anda dapat mengubah nilai nbins sesuai kebutuhan
#     ax2.yaxis.get_major_locator().set_params(nbins=5)
#     ax3.yaxis.get_major_locator().set_params(nbins=5)

def lowpass(data: np.ndarray, cutoff: float, sample_rate: float, poles: int = 5):
    sos = scipy.signal.butter(poles, cutoff, 'lowpass', fs=sample_rate, output='sos')
    filterResult = scipy.signal.sosfiltfilt(sos, data)
    return filterResult

def bandpass(data: np.ndarray, edges: list[float], sample_rate: float, poles: int = 5):
    sos = scipy.signal.butter(poles, edges, 'bandpass', fs=sample_rate, output='sos')
    filterResult = scipy.signal.sosfiltfilt(sos, data)
    return filterResult

def getData(i):
    global rawDataArray, filteredDataArray, startTime, nama, usia, gender, mode
    try:
        adcValue = sensor.readline().decode().strip()
        new_adc_values = [int(value) for value in adcValue.split(",")]
        # Menghapus 10 data pertama dari rawDataArray
        rawDataArray = rawDataArray[10:]
        # Menambahkan 10 data baru di akhir rawDataArray
        for value in new_adc_values:
            rawDataArray = np.append(rawDataArray, value)

        #Filtering
        if mode ==1 : filteredDataArray = lowpass(rawDataArray, 15, samplingRate)          # Low-pass filter
        if mode ==2 : filteredDataArray = bandpass(rawDataArray, [10, 40], samplingRate) # High-pass filter

        #update grafik rawdata
        line1.set_ydata(rawDataArray) 
        # # update grafik filtered 
        line2.set_ydata(filteredDataArray)
        line3.set_ydata(rawDataArray)
        line4.set_ydata(filteredDataArray)

        # Hitung BPM
        bpm = calculateBPM(filteredDataArray)

        # Update nilai BPM dan diagnosis
        if bpm < 60:
            diagnosis = "Bradikardia"
        elif bpm > 100:
            diagnosis = "Takikardia"
        else:
            diagnosis = "Normal"
        bpmText.set_text(f"BPM: {bpm} {diagnosis}")

        # if int(time.time()*1000) - startTime > samplingDuration*1000:
        #     updateYlimit()

        if uplinkInterval != 0 :
            if int(time.time()*1000) - startTime > uplinkInterval*1000:
                # Save dan sendData
                plt.savefig("chartResult.png", dpi=70)  # Mengatur DPI menjadi 100
                sendData(caption = f"Nama  : {nama}\nUsia     : {usia}\nL/P       : {gender}")

                # Simpan rawData
                fileNameCSV = nama+"_"+str(int(time.time()*1000))+".csv"
                fileNameWAV = nama+"_"+str(int(time.time()*1000))+".wav"

                df = pd.DataFrame({"Time" : timeLabel, "ADC" : rawDataArray})
                df.to_csv(fileNameCSV, index=False, sep=',')
                write(fileNameWAV, samplingRate, rawDataArray)

                startTime = int(time.time()*1000)

        return line1, line2, line3, line4, line5, bpmText
    
    except UnicodeDecodeError as e:
        print("Error decoding data:", e)
        
    return line1, line2, line3, line4, line5, bpmText

# Inisiasi serial port
portList = [port.device for port in serial.tools.list_ports.comports()]
while True:
    print("Port List :")
    for port in portList:
        print(port)
    print()
    
    usbPort = input("Pilih Port      : ")
    
    if usbPort in portList:
        break
    else:
        print("Port yang dimasukkan tidak tersedia. Silakan masukkan kembali.\n")
        portList = [port.device for port in serial.tools.list_ports.comports()]
        
sensor = serial.Serial(usbPort, 115200) 
uplinkInterval = int(input("Uplink Interval : "))
print("Mode :")
print("1. LPF (15hz)")
print("2. BPF (10hz-40Hz)")
mode = int(input("Pilih Mode       : "))
if mode == 1 :
    yLimit2 = yLimit1
    yLimit3 = yLimit1
    ax2.set_ylim(yLimit2)
    ax3.set_ylim(yLimit3)
nama   = input("Masukan Nama : ")
usia   = input("Usia         : ")
gender = input("Gender       : ") 
print("Tekan Enter untuk mulai")
input("")
# time.sleep(1)

startTime = int(time.time()*1000) #flag start sampling
ani = animation.FuncAnimation(fig, getData, frames=30, interval=0, blit=True) #loop getData
#Menampilkan grafik
plt.show()