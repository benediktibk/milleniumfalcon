from scipy.io import wavfile
import scipy as sp
import matplotlib.pylab as plt
import numpy
import random

random.seed(42)

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
driveLength = 39

for i in range(iterationSteps):
	start = i * iterationStepLengthInMs / 1000
	end = (i + 1) * iterationStepLengthInMs / 1000
	driveValue = numpy.mean([abs(x) for x in driveValues[int(start*samplingRate):int(end*samplingRate)]])
	
	if start > 20:
		driveValue = 1
	
	driveValuePerLed = [None] * driveLength
	
	for j in range(driveLength):
		driveValueRandomized = driveValue
		if start <= 20:
			driveValueRandomized = driveValueRandomized + random.randrange(-50, 30)/1000
			driveValueRandomized = max(0, driveValueRandomized)
			driveValueRandomized = min(1, driveValueRandomized)
		
		driveValuePerLed[j] = driveValueRandomized
	
	driveValuesNormalized[i] = driveValuePerLed

maximumDriveValue = max(max(driveValuesNormalized))

sequenceFile.write('turret;cockpit;front;landingGearAndRamp')

for i in range(driveLength):
	sequenceFile.write('drive-red-' + str(i) + ';')
	sequenceFile.write('drive-green-' + str(i) + ';')
	sequenceFile.write('drive-blue-' + str(i) + ';')

sequenceFile.write('\n')

for i in range(iterationSteps):
	start = i * iterationStepLengthInMs / 1000
	turretValue = 255
	cockpitValue = 255
	frontValue = 150
	landingGearAndRampValue = 255
	
	if start > 54 and start < 60 + 18:
		startFromErrorStart = start - 54
		withouFullSeconds = startFromErrorStart - int(startFromErrorStart)
		if withouFullSeconds > 0.5:
			cockpitValue = 0
	
	if start > 60 + 55:
		frontValue = 255
	
	sequenceFile.write(str(turretValue) + ';')
	sequenceFile.write(str(cockpitValue) + ';')
	sequenceFile.write(str(frontValue) + ';')
	sequenceFile.write(str(landingGearAndRampValue) + ';')
	
	for j in range(driveLength):
		driveValue = driveValuesNormalized[i][j] / maximumDriveValue
		redChannel = driveColorRed
		greenChannel = driveColorGreen
		blueChannel = driveColorBlue
		
		useBadValue = random.randrange(0, 200) < 1
		if start <= 60 + 55 and useBadValue:
			redChannel = driveColorRedBad
			greenChannel = driveColorGreenBad
			blueChannel = driveColorBlueBad
		
		valueRed = driveValue * redChannel
		valueGreen = driveValue * greenChannel
		valueBlue = driveValue * blueChannel
		
		sequenceFile.write(str(int(valueRed)) + ';' + str(int(valueGreen)) + ';' + str(int(valueBlue)) + ';')
	sequenceFile.write('\n')

sequenceFile.close()