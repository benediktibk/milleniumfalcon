#!/usr/bin/env python3

import signal
import time
import logging
import pygame
from gpiozero import Button,PWMLED,LED
from ctypes import cdll, byref, create_string_buffer

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
		pygame.mixer.init()
		
	def __enter__(self):
		return self
		
	def __exit__(self, exc_type, exc_value, traceback):
		self.stop()
		
	def play(self, audioFile):
		pygame.mixer.music.load(audioFile)
		pygame.mixer.music.play()
		
	def stop(self):
		pygame.mixer.music.stop()
		
class Peripherals:
	_mainSwitch = LED(17)
	_cockpit = PWMLED(27)
	_turret = PWMLED(22)
	_front = PWMLED(4)
	
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
	
	def compensateOutputCharacteristics(self, value):
		logger.debug('compensating output characteristic for value ' + '{:.2f}'.format(value))
		if value < 0 or value > 1:
			raise ValueError('the value for an output must be within the range 0 and 1')
		
		value = 1 - value
		
		logger.debug('compensated value is ' + '{:.2f}'.format(value))
		return value
		
	def setCockpit(self, value):
		logger.debug('setting value ' + '{:.2f}'.format(value) + ' for cockpit')
		value = self.compensateOutputCharacteristics(value)
		self._cockpit.value = value
		
	def setTurret(self, value):
		logger.debug('setting value ' + '{:.2f}'.format(value) + ' for turret')
		value = self.compensateOutputCharacteristics(value)
		self._turret.value = value
		
	def setFront(self, value):
		logger.debug('setting value ' + '{:.2f}'.format(value) + ' for front')
		value = self.compensateOutputCharacteristics(value)
		self._front.value = value
		
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

if __name__ == '__main__':
	signalHandler = SignalHandler()
	
	with Peripherals() as peripherals:
		while True:
			for x in range(0, 100):
				value = x/100
				peripherals.setFront(value)
				time.sleep(0.1)

			if signalHandler.checkIfShouldBeStopped():
				break

	logger.info("stopping gracefully")