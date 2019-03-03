#!/usr/bin/env python3

import signal
import time
import logging
import pygame
import re
from gpiozero import Button,PWMLED,LED
from ctypes import cdll, byref, create_string_buffer
from math import exp
from neopixel import Adafruit_NeoPixel, Color

logger = logging.getLogger()
handler = logging.FileHandler("/var/log/falcon-service")
formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

def setprocessname(processname):	
	libc = cdll.LoadLibrary('libc.so.6')
	buff = create_string_buffer(len(processname) + 1)
	buff.value = processname
	libc.prctl(15, byref(buff), 0, 0, 0)

logger.debug("set process name")
setprocessname(b"falcon-service")

class SignalHandler:
	_shouldStop = False
	
	def __init__(self):
		signal.signal(signal.SIGINT, self.stop)
		signal.signal(signal.SIGTERM, self.stop)

	def stop(self, signum, frame):
		logger.info("received signal to stop")
		self._shouldStop = True
		
	def checkIfShouldBeStopped(self):
		return self._shouldStop
		
class AudioPlayer:
	def __init__(self):
		logger.info("initializing audio player")
		pygame.mixer.init()
		
	def __enter__(self):
		return self
		
	def __exit__(self, exc_type, exc_value, traceback):
		logger.info("destroying audio player")
		self.stop()
		
	def play(self, audioFile):
		logger.info("starting to play " + audioFile)
		pygame.mixer.music.load(audioFile)
		pygame.mixer.music.play()
		
	def stop(self):
		logger.info("stopping audio playback")
		pygame.mixer.music.stop()
		
class LedStrip:
	_ledCount = 100
	_ledPin = 18
	_ledFrequency = 800000
	_ledDma = 10
	_ledInvert = False
	_ledBrightness = 255
	_ledChannel = 0
	
	def __init__(self):
		logger.info("initializing led strip")
		self._ledStrip = Adafruit_NeoPixel(self._ledCount, self._ledPin, self._ledFrequency, self._ledDma, self._ledInvert, self._ledBrightness, self._ledChannel)
		self._ledStrip.begin()
		
	def __enter__(self):
		return self
		
	def __exit__(self, exc_type, exc_value, traceback):
		logger.info("destroying led strip")
		self.turnOff()
		
	def turnOff(self):
		logger.info("turning all pixel off")
		for i in range(self._ledCount):
			self._ledStrip.setPixelColor(i, Color(0, 0, 0))
		self._ledStrip.show()
		
	def setPixelColor(self, pixel, color):
		logger.info("setting color for pixel " + str(pixel))
		if pixel < 0 or pixel >= self._ledCount:
			raise ValueError('the pixel index must be within 0 and ' + str(self._ledCount))
		self._ledStrip.setPixelColor(pixel, color)
		self._ledStrip.show()
		
class Peripherals:
	_mainSwitch = LED(17)
	_cockpit = PWMLED(27)
	_turret = PWMLED(22)
	_front = PWMLED(4)
	_landingGearAndRamp = PWMLED(25)
	_drive = LedStrip()
	_start = Button(23)
	
	def __init__(self):
		logger.info("initializing peripherals")
		self.setAll(0)
		self.turnOn()
		
	def __enter__(self):
		return self
		
	def __exit__(self, exc_type, exc_value, traceback):
		logger.info("destroying peripherals")
		self.setAll(0)
		self.turnOff()
		self._drive.__exit__(exc_type, exc_value, traceback)
	
	def compensateOutputCharacteristics(self, value):
		logger.debug('compensating output characteristic for value ' + '{:.2f}'.format(value))
		if value < 0 or value > 1:
			raise ValueError('the value for an output must be within the range 0 and 1')
		
		value = 1 - value
		nonlinearBase = 100
		value = (nonlinearBase**value)/(nonlinearBase**1)
		logger.debug('compensated value is ' + '{:.2f}'.format(value))
		return value
		
	def setCockpit(self, value):
		logger.debug('setting value ' + '{:.2f}'.format(value) + ' for cockpit')
		compensatedValue = self.compensateOutputCharacteristics(value)
		self._cockpit.value = compensatedValue
		
	def setTurret(self, value):
		logger.debug('setting value ' + '{:.2f}'.format(value) + ' for turret')
		compensatedValue = self.compensateOutputCharacteristics(value)
		self._turret.value = compensatedValue
		
	def setFront(self, value):
		logger.debug('setting value ' + '{:.2f}'.format(value) + ' for front')
		compensatedValue = self.compensateOutputCharacteristics(value)
		self._front.value = compensatedValue
		
	def setLandingGearAndRamp(self, value):
		logger.debug('setting value ' + '{:.2f}'.format(value) + ' for landing gear and ramp')
		compensatedValue = self.compensateOutputCharacteristics(value)
		self._landingGearAndRamp.value = compensatedValue
		
	def setAll(self, value):
		self.setCockpit(value)
		self.setTurret(value)
		self.setFront(value)
		self.setLandingGearAndRamp(value)
		
	def turnOff(self):
		logger.info('turning main switch off')
		self._mainSwitch.off()
		
	def turnOn(self):
		logger.info('turning main switch on')
		self._mainSwitch.on()
		
	def setDrive(self, pixel, color):
		self._drive.setPixelColor(pixel, color)
		
	def shouldRun(self):
		return self._start.is_pressed
		
class SequenceStep:
	_turret = 0
	_cockpit = 0
	_front = 0
	_landingGearAndRamp = 0
	_drive = []
	
	def __init__(self, values):
		self._turret = values[0]
		self._cockpit = values[1]
		self._front = values[2]
		self._landingGearAndRamp = values[3]
		driveLedCount = int((len(values) - 4)/3)
		self._drive = [None] * driveLedCount
		
		for i in range(driveLedCount):
			self._drive[i] = [values[4 + i*3], values[5 + i*3], values[6 + i*3]]
	
	def applyTo(self, peripherals):
		peripherals.setTurret(self._turret)
		peripherals.setCockpit(self._cockpit)
		peripherals.setFront(self._front)
		peripherals.setLandingGearAndRamp(self._landingGearAndRamp)
		
		for i in range(len(_drive)):
			peripherals.setDrive(i, Color(drive[i][0], drive[i][1], drive[i][2]))
	
class Sequence:
	_steps = []
	
	def __init__(self, fileName):
		sequenceFile = file.open(fileName, 'r')
		header = sequenceFile.readline()
		driveOccurences = re.findall('drive-red-[0-9]*', header)
		driveLedCount = len(driveOccurences)
		lines = sequenceFile.readlines()
		lines = [x.strip() for x in lines]
		_steps = [None] * len(lines)
		
		for i in range(len(lines)):
			values = re.findall('[0-9]*', lines(i))
			self._steps[i] = SequenceStep(values)		
		
		sequenceFile.close()
		
	def applyTo(self, peripherals, step):
		self._steps[step].applyTo(peripherals)
		
	def getStepCount(self):
		return len(self._steps)
	
class Falcon:
	_sequenceExecuted = False
	_iterationStepInMilliseconds = 200

	def __init__(self, signalHandler):
		logger.info("initializing led falcon")
		self._peripherals = Peripherals()
		self._audioPlayer = AudioPlayer()
		self._signalHandler = signalHandler
		self._sequence = Sequence('/usr/share/falcon/sequence.csv')
		
	def __enter__(self):
		return self
		
	def __exit__(self, exc_type, exc_value, traceback):
		self._peripherals.__exit__(exc_type, exc_value, traceback)
		self._audioPlayer.__exit__(exc_type, exc_value, traceback)
		
	def bootSequence(self):
		logger.info('starting boot sequence')
		self._audioPlayer.play('/usr/share/falcon/audio/bootup_sequence_initialized.wav')
		time.sleep(2.4)
		
		for x in range(0, 10):
			value = x/10
			self._peripherals.setFront(value)
			time.sleep(0.1)
		self._peripherals.setFront(0)
		
		for x in range(0, 10):
			value = x/10
			self._peripherals.setCockpit(value)
			time.sleep(0.1)
		self._peripherals.setCockpit(0)
		
		for x in range(0, 10):
			value = x/10
			self._peripherals.setTurret(value)
			time.sleep(0.1)
		self._peripherals.setTurret(0)
		
		for x in range(0, 10):
			self._peripherals.setDrive(x, Color(255, 255, 255))
			time.sleep(0.1)
			self._peripherals.setDrive(x, Color(0, 0, 0))
		
		self._audioPlayer.play('/usr/share/falcon/audio/bootup_sequence_finished.wav')
		time.sleep(3.5)
		logger.info('finished boot sequence')
		
	def runOnce(self):
		if not self._peripherals.shouldRun():n
			self._sequenceExecuted = False
			return
			
		if self._sequenceExecuted:
			return
			
		logger.info('sequence should run')
		self._audioPlayer.play('/usr/share/falcon/audio/take_off.wav')
		
		start = time.time()
		
		while True:
			iterationStep = self.__calculateIterationStep(start)
			
			if (iterationStep >= self._sequence.getStepCount())
				break
			
			logger.info('iteration step ' + str(iterationStep) + ' of ' + str(self._sequence.getStepCount()))
			self._sequence.applyTo(self._peripherals, iterationStep)
			
			waitTime = (((iterationStep + 1) * self.__iterationStepInMilliseconds)/1000 + start) - current
			logger.info('waiting for ' + '{:.3f}'.format(waitTime) + 's')
			time.sleep(waitTime)
			
			if not self._peripherals.shouldRun():
				logger.info('sequence should stop due to user input')
				break
			
			if self._signalHandler.checkIfShouldBeStopped():
				logger.info('sequence should stop due to system signal')
				break
		
		self._peripherals.turnOff()
		self._audioPlayer.stop()
		self._sequenceExecuted = True
		
	def __calculateIterationStep(self, start)
		current = time.time()
		return int((current - start)*1000/self._iterationStepInMilliseconds)

if __name__ == '__main__':
	signalHandler = SignalHandler()
	
	with Falcon(signalHandler) as falcon:
		falcon.bootSequence()
		
		while not signalHandler.checkIfShouldBeStopped():
			falcon.runOnce()
			time.sleep(0.2)

	logger.info("stopping gracefully")