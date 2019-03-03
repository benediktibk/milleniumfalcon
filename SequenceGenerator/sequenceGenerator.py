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
timeValues = [float(timeValue) / samplingRate for timeValue in list(range(dataPoints))]

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
iterationStepLengthInMs = 200
sequenceFile = open('../MilleniumFalconClient/sequence.csv', 'w')
iterationSteps = int(dataPoints/samplingRate*(1000/iterationStepLengthInMs)) - 1
driveValuesNormalized = [None] * iterationSteps
driveColorRed = 200
driveColorGreen = 255
driveColorBlue = 255
driveColorRedBad = 255
driveColorGreenBad = 0
driveColorBlueBad = 0
driveLength = 10

for i in range(iterationSteps):
	start = i * iterationStepLengthInMs / 1000
	end = (i + 1) * iterationStepLengthInMs / 1000
	driveValue = numpy.mean([abs(x) for x in driveValues[int(start*samplingRate):int(end*samplingRate)]])
	driveValuePerLed = [None] * driveLength
	
	for j in range(driveLength):
		driveValuePerLed[j] = driveValue
	
	driveValuesNormalized[i] = driveValuePerLed

maximumDriveValue = max(max(driveValuesNormalized))

sequenceFile.write('iteration;turret;cockpit;')

for i in range(driveLength):
	sequenceFile.write('drive-red-' + str(i) + ';')
	sequenceFile.write('drive-green-' + str(i) + ';')
	sequenceFile.write('drive-blue-' + str(i) + ';')

sequenceFile.write('\n')

for i in range(iterationSteps):
	sequenceFile.write(str(i) + ';')
	sequenceFile.write(str(255) + ';')
	sequenceFile.write(str(255) + ';')
	
	for j in range(driveLength):
		driveValue = driveValuesNormalized[i][j] / maximumDriveValue
		sequenceFile.write(str(int(driveValue * driveColorRed)) + ';' + str(int(driveValue * driveColorGreen)) + ';' + str(int(driveValue * driveColorBlue)) + ';')
	sequenceFile.write('\n')

sequenceFile.close()