import os
import subprocess
import time
import tempfile

out, path = tempfile.mkstemp()
print path

#subprocess.Popen('test.sh', shell=True).wait()
proc = subprocess.Popen('test.sh 6', stdout=out, shell=True)
output = open(path)
print output.fileno()
while proc.poll() is None:
    print output.read(),
    time.sleep(1)

os.unlink(path)
