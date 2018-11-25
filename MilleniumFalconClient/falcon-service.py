#!/usr/bin/env python3

import signal
import time
import logging
import pygame
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
			raise ValueError('the pixel index must be within 0 and ' + self._ledCount)
		self._ledStrip.setPixelColor(pixel, color)
		self._ledStrip.show()
		
class Peripherals:
	_mainSwitch = LED(17)
	_cockpit = PWMLED(27)
	_turret = PWMLED(22)
	_front = PWMLED(4)
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
		
	def setAll(self, value):
		self.setCockpit(value)
		self.setTurret(value)
		self.setFront(value)
		
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
		
if __name__ == '__main__':
	signalHandler = SignalHandler()
	
	with Peripherals() as peripherals:
		with AudioPlayer() as audioPlayer:
			while True:
				if peripherals.shouldRun():
					logger.info('starting sequence')
					peripherals.turnOn()
					
					audioPlayer.play('/root/example.wav')
					
					while peripherals.shouldRun():
						for x in range(0, 10):
							value = x/10
							peripherals.setFront(value)
							peripherals.setDrive(x, Color(255, 255, 255))
							time.sleep(0.2)
							peripherals.setDrive(x, Color(0, 0, 0))

						if signalHandler.checkIfShouldBeStopped():
							break
					
					logger.info('stopping sequence')
					peripherals.turnOff()
					audioPlayer.stop()
				else:
					time.sleep(0.1)
				
				if signalHandler.checkIfShouldBeStopped():
					break

	logger.info("stopping gracefully")
	time.sleep(1)