#!/usr/bin/env python3

from subprocess import call
from shutil import copyfile

sourcePath = "/usr/src/milleniumfalcon
falconUpdate = "/usr/bin/falcon-update.py"

print("checkout repository")
check_call(["git", "fetch"], cwd=sourcePath)
check_call(["git", "checkout", "master"], cwd=sourcePath)

print("update scripts")
copyfile(sourcePath + "/MilleniumFalconClient/falcon-update.py", falconUpdate)

print("set owner of scripts")
call(["chown", "root:root", falconUpdate)

print("make scripts executable")
call(["chmod", "755", falconUpdate)