#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from distutils.core import setup
import py2exe, sys
from glob import glob
sys.path.append("C:\\Temp\\Microsoft.VC90.CRT")
data_files = [("Microsoft.VC90.CRT", glob(r'C:\Temp\Microsoft.VC90.CRT\*.*'))]
setup(
    data_files=data_files,
    console=['ride.py'])
