from pandas import DataFrame 
import pandas as pd
import numpy as np
from numpy import diff
from scipy.stats import linregress
from scipy.signal import butter, lfilter, freqz
import matplotlib.pyplot as plt

df = pd.read_csv('/Users/twitter/Desktop/Python Projects/Sample Data/Sample_ECG5.txt', delimiter = "\t", index_col=0)
frame = DataFrame(df)

df.columns=['ecg', 'bp', 'time2']
ECG = frame['ecg']

#Low pass filter for ECG signal
def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

Filtered_ECG = butter_lowpass_filter(ECG, 3.667, 1000.0, order=5)

# Filter requirements.
order = 6
fs = 30.0       # sample rate, Hz
cutoff = 3.667  # desired cutoff frequency of the filter, Hz

# Get the filter coefficients so we can check its frequency response.
b, a = butter_lowpass(cutoff, fs, order)

frame2 = DataFrame(df, columns=['ecg', 'bp', 'time2', 'filtered_ecg'])
frame2['filtered_ecg'] = Filtered_ECG

#QRS threshold 
threshold = (np.max(frame2.filtered_ecg) - (np.max(frame2.filtered_ecg)-np.min(frame2.filtered_ecg))*.2)

#QRS detection
ind = 0
ind2 = 0
hbindex = [frame2.index[0]]
heartbeat = []
RRindex = []
hbs = [0]
timestamp = []
for x in Filtered_ECG:
    ind += 1
    if x > threshold and Filtered_ECG[ind-1] > Filtered_ECG[(ind-1)-1] and Filtered_ECG[ind-1] > Filtered_ECG[(ind-1)+1]:  
        ind2 += 1
        hbs.append(ind2)
        heartbeat.append(ind2)
        hbindex.append(frame2.index[ind]) #timestamp for all detectected QRS in ECG
    else:
        heartbeat.append(ind2)

frame2['heart_beat'] = heartbeat
frame2.index.names = ['time']

#Heart Rate
RR = np.diff(hbindex)
HR = 60/RR
RR[0] = RR[1]
HR[0] = HR[1]

#beat to beat BP values for each QRS
sbp = []
mbp = []
dbp = []
for x in hbs:
    sbp.append(np.max(frame2[frame2.heart_beat == x].bp))
    mbp.append(np.mean(frame2[frame2.heart_beat == x].bp))
    dbp.append(np.min(frame2[frame2.heart_beat == x].bp))

#Output dataframe
frame3 = DataFrame(hbs[1:], columns = ['hb'])
frame3['time'] = hbindex[1:]
frame3['RR'] = RR
frame3['HR'] = HR
frame3['sbp'] = sbp[1:]
frame3['mbp'] = mbp[1:]
frame3['dbp'] = dbp[1:]

#Binning by SBP
BPbin= []
for y in frame3.sbp:
    BPbin.append(int((y - min(frame3.sbp))/3))
frame3['bin'] = BPbin

#frame3['time'] = frame3.time - min(frame3.time)
frame3 = frame3[:123] 
print frame3

groupedRR = frame3['RR'].groupby(frame3['bin'])
print groupedRR.mean()
RRarray = [groupedRR.mean()]

groupedHR = frame3['HR'].groupby(frame3['bin'])
print groupedHR.mean()
HRarray = [groupedHR.mean()]

groupedSBP = frame3['sbp'].groupby(frame3['bin'])
print groupedSBP.mean()
SBParray = [groupedSBP.mean()]

print "bin size", groupedSBP.size()
bin_weight = groupedSBP.size()/123
print "bin weight", bin_weight 

#linear regression
slope, intercept, r_value, p_value, std_err = linregress(SBParray, HRarray)
print "slope", slope
print "r squared", r_value**2
print "p", p_value

slope, intercept, r_value, p_value, std_err = linregress(SBParray, RRarray)
print "slope", slope
print "r squared", r_value**2
print "p", p_value

#plots plots plots plots plots plots plots plots plots plots plots
fig = plt.figure()

#ECG plot
ax1 = fig.add_subplot(2, 1, 1)
plt.plot(frame2.index, frame2.filtered_ecg)
plt.plot(frame3.time, frame2.filtered_ecg[frame3.time], linestyle=' ', marker='o')

#blood pressure plot
ax2 = fig.add_subplot(2, 1, 2)
plt.xlabel('Time, s')
plt.plot(frame2.index, frame2.bp)
plt.plot(frame3.time, frame3.sbp)
plt.plot(frame3.time, frame3.mbp)
plt.plot(frame3.time, frame3.dbp)
plt.ylabel('Blood Pressure')
fig2 = plt.figure()

#correlation plots
#HR vs SBP 
ax3 = fig2.add_subplot(1, 1, 1)
plt.plot(SBParray, HRarray, linestyle=' ', marker='.')
plt.ylabel('Heart Rate')
plt.xlabel('Systolic Blood Pressure')

#RR vs SBP 
fig3 = plt.figure()
ax4 = fig3.add_subplot(1, 1, 1)
plt.plot(SBParray, RRarray, linestyle=' ', marker='.') 
plt.ylabel('RR interval')
plt.xlabel('Systolic Blood Pressure')