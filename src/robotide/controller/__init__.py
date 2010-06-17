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

import os

from robot.parsing.model import TestCaseFile, TestDataDirectory
from filecontroller import DataController, ResourceFileController, UserKeywordController
from chiefcontroller import ChiefController


def NewDatafile(path, is_dir_type):
    return _new_datadirectory(path) if is_dir_type else _new_datafile(path)

def _new_datadirectory(path):
    data = TestDataDirectory()
    path = os.path.abspath(path)
    data.source = os.path.dirname(path)
    data.directory = data.source
    data.initfile = path
    _create_missing_dirs(data.directory)
    return data

def _new_datafile(path):
    data = TestCaseFile()
    data.source = os.path.abspath(path)
    data.directory = os.path.dirname(data.source)
    _create_missing_dirs(data.directory)
    return data

def _create_missing_dirs(dirpath):
    if not os.path.isdir(dirpath):
        os.makedirs(dirpath)
