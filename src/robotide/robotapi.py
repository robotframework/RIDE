#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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

from robot.utils import version as ROBOT_VERSION
from robot.utils import normpath, NormalizedDict
from robot.parsing import TestSuite as TestSuiteData
from robot.parsing import ResourceFile as ResourceFileData
from robot.running import TestLibrary
from robot.output import LOGGER as ROBOT_LOGGER
from robot.variables import Variables as RobotVariables
from robot.variables import is_scalar_var, is_list_var, is_var

import robot.parsing.rawdata
robot.parsing.rawdata.PROCESS_CURDIR = False

from robot.parsing.model import DirectorySuite


class InitFileData(DirectorySuite):
    
    def __init__(self, path):
        DirectorySuite.__init__(self, path, [])
        
    def _process_subsuites(self, paths, suitenames, syslog):
        pass
    
    def get_test_count(self):
        return 1

