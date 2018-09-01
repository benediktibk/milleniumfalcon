#!/usr/bin/env python3

from subprocess import call,check_call
from shutil import copyfile

sourcePath = "/usr/src/milleniumfalcon"
falconUpdate = "/usr/bin/falcon-update.py"
falconService = "/usr/bin/falcon-service.py"
falconServiceInitScript = "/etc/init.d/falcon-service"

print("checkout repository")
check_call(["git", "fetch", "--force"], cwd=sourcePath)
check_call(["git", "pull", "--force"], cwd=sourcePath)

print("update scripts")
copyfile(sourcePath + "/MilleniumFalconClient/falcon-update.py", falconUpdate)
copyfile(sourcePath + "/MilleniumFalconClient/falcon-service.py", falconService)
copyfile(sourcePath + "/MilleniumFalconClient/falcon-service.py", falconServiceInitScript)

print("set owner of scripts")
call(["chown", "root:root", falconUpdate])
call(["chown", "root:root", falconService])
call(["chown", "root:root", falconServiceInitScript])

print("make scripts executable")
call(["chmod", "755", falconUpdate])
call(["chmod", "755", falconService])
call(["chmod", "755", falconServiceInitScript])

print("create pid files if necessary")
call(["touch", "/var/run/falcon-service.pid"])