from scipy.io import wavfile
import scipy as sp
import matplotlib.pylab as plt
import numpy

print('read in source file')
samplingRate, data = wavfile.read('../MilleniumFalconClient/audio/take_off.wav')
dataPoints = len(data)
leftAndRightCombined = [None] * dataPoints

print('combine left and right into one channel')
for i in range(dataPoints):
	leftAndRightCombined[i] = (float(data[i][0]) + float(data[i][1]))/2
	
maximumValue = max(leftAndRightCombined)
leftAndRightCombined = [value/maximumValue for value in leftAndRightCombined]
timeValues = [float(timeValue) / 8000 for timeValue in list(range(dataPoints))]

print('execute frequency analysis')
frequencies = [numpy.real(value) for value in numpy.fft.rfft(leftAndRightCombined)]
cutOffFrequency = 50000
driveCutOffFrequency = 50000
driveFrequencies = frequencies.copy()
for i in range(driveCutOffFrequency, len(driveFrequencies)):
	driveFrequencies[i] = 0
driveValues = numpy.fft.irfft(driveFrequencies)

print('create plots')
plt.subplot(2, 2, 1)
plt.plot(timeValues, leftAndRightCombined)
plt.subplot(2, 2, 3)
plt.plot(list(range(cutOffFrequency)), frequencies[:cutOffFrequency])
plt.subplot(2, 2, 2)
plt.plot(timeValues, driveValues)
plt.show()

print('create output files')
wavfile.write('C:/Temp/drive.wav', samplingRate, driveValues)

#for i in range(len(data)):
#	print(str(data[i][0]) + '-' + str(data[i][1]))