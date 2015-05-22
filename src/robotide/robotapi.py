#  Copyright 2008-2015 Nokia Solutions and Networks
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

import robot.parsing.populators
robot.parsing.populators.PROCESS_CURDIR = False

from robot.errors import DataError
from robot.model import TagPatterns
from robot.output import LOGGER as ROBOT_LOGGER
from robot.parsing.datarow import DataRow
from robot.parsing.model import (TestCase, TestDataDirectory, ResourceFile,
    TestCaseFile, UserKeyword, Variable, Step, ForLoop)
from robot.parsing.populators import FromFilePopulator
from robot.parsing.settings import Library, Resource, Variables, Comment
from robot.parsing.tablepopulators import (UserKeywordPopulator,
    TestCasePopulator)
from robot.parsing.txtreader import TxtReader
from robot.running import TestLibrary
from robot.running.namespace import STDLIB_NAMES
from robot.running.usererrorhandler import UserErrorHandler
from robot.running.userkeyword import EmbeddedArgsTemplate
from robot.utils import normpath, NormalizedDict
from robot.variables import Variables as RobotVariables
from robot.variables import is_scalar_var, is_list_var, is_var, VariableSplitter
from robot.version import get_version

ROBOT_VERSION = get_version()
