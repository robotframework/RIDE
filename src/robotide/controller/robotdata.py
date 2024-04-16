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

import os

from .. import robotapi


def get_language_from_settings():
    from ..preferences import RideSettings
    _settings = RideSettings()
    lang = _settings.get('doc language', '')
    return lang


def new_test_case_file(path, tasks=False, lang=None):
    lang = lang if lang else get_language_from_settings()
    if not isinstance(lang, list):
        lang = [lang]
    datafile = robotapi.TestCaseFile(source=path, tasks=tasks, language=lang)
    datafile.set_doc_language()
    header = 'Tasks' if tasks else 'Test Cases'
    datafile.start_table([header], lineno=1, llang=lang)  # It is the unique section, so no problem
    _create_missing_directories(datafile.directory)
    return datafile


def new_test_data_directory(path, tasks=False, lang=None):
    lang = lang if lang else get_language_from_settings()
    if not isinstance(lang, list):
        lang = [lang]
    dirname = os.path.dirname(path)
    datafile = robotapi.TestDataDirectory(source=dirname, tasks=tasks, language=lang)
    datafile.set_doc_language()
    datafile.initfile = path
    _create_missing_directories(dirname)
    return datafile


def _create_missing_directories(dirname):
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
