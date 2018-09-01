#!/usr/bin/env python3

import signal
import time
import logging
import pygame
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
	
	def play(audioFile):
		pygame.mixer.music.load(audioFile)
		pygame.mixer.music.play()
		
	def stop():
		pygame.mixer.music.stop()

if __name__ == '__main__':
	signalHandler = SignalHandler()
	audioPlayer = AudioPlayer()
	
	audioPlayer.start("/tmp/example.wav")
	
	while True:
		time.sleep(0.1)
		if signalHandler.checkIfShouldBeStopped():
			break

logger.info("stopping gracefully")