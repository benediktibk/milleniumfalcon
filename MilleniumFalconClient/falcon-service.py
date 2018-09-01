#!/usr/bin/env python3

import signal
import time
import logging


logger = logging.getLogger()
handler = logging.FileHandler("/var/log/falcon-service")
formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

logger.debug("set process name")
procname.setprocname("falcon-service")

class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, signum, frame):
    logger.info("received signal to stop")
    self.kill_now = True

if __name__ == '__main__':
  killer = GracefulKiller()
  while True:
    time.sleep(1)
    logger.info("doing something important")
    if killer.kill_now:
      break

logger.info("stopping gracefully")