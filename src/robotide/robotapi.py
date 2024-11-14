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

from .lib.robot.parsing import populators
from .lib.robot.errors import DataError, VariableError, Information
from .lib.robot.model import TagPatterns
from .lib.robot.output import LOGGER as ROBOT_LOGGER
# SEE BELOW
# from .lib.robot.output.loggerhelper import LEVELS as LOG_LEVELS
from .lib.robot.parsing.datarow import DataRow
from .lib.robot.parsing.model import (
    TestCase, TestDataDirectory, ResourceFile, TestCaseFile, UserKeyword,
    Variable, Step, ForLoop, VariableTable, KeywordTable, TestCaseTable,
    TestCaseFileSettingTable)
from .lib.robot.parsing.populators import FromFilePopulator
from .lib.robot.parsing.settings import (Library, Resource, Variables, Comment, ImportSetting, Template, Fixture,
                                         Documentation, Timeout, Tags, Return, Setting)
from .lib.robot.parsing.tablepopulators import UserKeywordPopulator, TestCasePopulator
from .lib.robot.parsing.robotreader import RobotReader
from .lib.robot.running import TestLibrary, EXECUTION_CONTEXTS
from .lib.robot.libraries import STDLIBS as STDLIB_NAMES
from  platform import python_version
if python_version() >= '3.13':
    STDLIB_NAMES = STDLIB_NAMES.difference(['Telnet'])
from .lib.robot.running.usererrorhandler import UserErrorHandler
from .lib.robot.running.arguments.embedded import EmbeddedArgumentParser
from .lib.robot.utils import normpath, NormalizedDict
from .lib.robot.variables import Variables as RobotVariables
from .lib.robot.variables import is_scalar_var, is_list_var, is_var, is_dict_var, VariableSplitter
from .lib.robot.variables.tablesetter import VariableTableReader
from .lib.robot.version import ROBOT_VERSION, ALIAS_MARKER
from .lib.robot.variables.filesetter import VariableFileSetter

populators.PROCESS_CURDIR = False

# Monkey patch LEVELS
LOG_LEVELS = {
  'NONE': 7,
  'SKIP': 6,
  'FAIL': 5,
  'ERROR': 4,
  'WARN': 3,
  'INFO': 2,
  'DEBUG': 1,
  'TRACE': 0,
}
