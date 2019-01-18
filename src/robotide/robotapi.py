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

import robotide.lib.robot.parsing.populators
robotide.lib.robot.parsing.populators.PROCESS_CURDIR = False

from robotide.lib.robot.errors import DataError, VariableError, Information
from robotide.lib.robot.model import TagPatterns
from robotide.lib.robot.output import LOGGER as ROBOT_LOGGER
from robotide.lib.robot.output.loggerhelper import LEVELS as LOG_LEVELS
from robotide.lib.robot.parsing.datarow import DataRow
from robotide.lib.robot.parsing.model import (
    TestCase, TestDataDirectory, ResourceFile, TestCaseFile, UserKeyword,
    Variable, Step, ForLoop, VariableTable, KeywordTable, TestCaseTable,
    TestCaseFileSettingTable)
from robotide.lib.robot.parsing.populators import FromFilePopulator
from robotide.lib.robot.parsing.settings import (
    Library, Resource, Variables, Comment, _Import, Template,
    Fixture, Documentation, Timeout, Tags, Return)
from robotide.lib.robot.parsing.tablepopulators import (
    UserKeywordPopulator, TestCasePopulator)
from robotide.lib.robot.parsing.txtreader import TxtReader
from robotide.lib.robot.running import TestLibrary, EXECUTION_CONTEXTS
from robotide.lib.robot.libraries import STDLIBS as STDLIB_NAMES
from robotide.lib.robot.running.usererrorhandler import UserErrorHandler
from robotide.lib.robot.running.arguments.embedded import EmbeddedArgumentParser
from robotide.lib.robot.utils import normpath, NormalizedDict
from robotide.lib.robot.variables import Variables as RobotVariables
from robotide.lib.robot.variables import is_scalar_var, is_list_var, is_var, is_dict_var,\
    VariableSplitter
from robotide.lib.robot.variables.filesetter import VariableFileSetter
from robotide.lib.robot.variables.tablesetter import VariableTableReader
from robotide.lib.robot.version import get_version

ROBOT_VERSION = get_version()
