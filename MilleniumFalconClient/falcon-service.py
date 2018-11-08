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
		self.setAll(0)
		self.turnOn()
		
	def __enter__(self):
		return self
		
	def __exit__(self, exc_type, exc_value, traceback):
		self.setAll(0)
		self.turnOff()
		
	def setCockpit(self, value):
		self._cockpit.value = value
		
	def setTurret(self, value):
		self._turret.value = value
		
	def setFront(self, value):
		self._front.value = value
		
	def setAll(self, value):
		self.setLandingLights(value)
		self.setRamp(value)
		self.setCockpit(value)
		self.setTurret(value)
		self.setFront(value)
		
	def turnOff(self):
		_mainSwitch.off()
		
	def turnOn(self):
		_mainSwitch.on()

if __name__ == '__main__':
	signalHandler = SignalHandler()
	
	with Peripherals() as peripherals:
		while True:
			for x in range(0, 100):
					value = x/100
					logger.info('setting value ' + '{:.2f}'.format(value))
					peripherals.setFront(value)
					time.sleep(0.1)

			if signalHandler.checkIfShouldBeStopped():
				break

	logger.info("stopping gracefully")