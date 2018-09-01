#!/usr/bin/env python3

from subprocess import call,check_call
from shutil import copyfile

sourcePath = "/usr/src/milleniumfalcon"
falconUpdate = "/usr/bin/falcon-update.py"
falconService = "/usr/bin/falcon-service.py"
falconServiceInitScript = "/etc/init.d/falcon-service"
falconServiceLogFile = "/var/log/falcon-service"

print("checkout repository")
check_call(["git", "fetch", "--force"], cwd=sourcePath)
check_call(["git", "pull", "--force"], cwd=sourcePath)

print("update scripts")
copyfile(sourcePath + "/MilleniumFalconClient/falcon-update.py", falconUpdate)
copyfile(sourcePath + "/MilleniumFalconClient/falcon-service.py", falconService)
copyfile(sourcePath + "/MilleniumFalconClient/falcon-service", falconServiceInitScript)

print("set owner of scripts")
call(["chown", "root:root", falconUpdate])
call(["chown", "root:root", falconService])
call(["chown", "root:root", falconServiceInitScript])

print("set filesystem rights of scripts")
call(["chmod", "755", falconUpdate])
call(["chmod", "755", falconService])
call(["chmod", "755", falconServiceInitScript])

print("create pid files if necessary")
call(["touch", "/var/run/falcon-service.pid"])

print("create log files if necessary")
call(["touch", falconServiceLogFile])

print("set owner of log files")
call(["chown", "falcon-service", falconServiceLogFile])

print("set filesystem rights of log files")
call(["chmod", "644", falconServiceLogFile])

print("install services")
call(["update-rc.d", "falcon-service", "defaults"])

print("configure logrotate")
copyfile(sourcePath + "/MilleniumFalconClient/falcon-logrotate", "/etc/logrotate.d/falcon")