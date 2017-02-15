from distutils.core import setup
import py2exe, sys
from glob import glob
sys.path.append("C:\\Temp\\Microsoft.VC90.CRT")
data_files = [("Microsoft.VC90.CRT", glob(r'C:\Temp\Microsoft.VC90.CRT\*.*'))]
setup(
    data_files=data_files,
    console=['ride.py'])
