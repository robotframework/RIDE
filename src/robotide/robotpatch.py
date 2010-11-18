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

'''
This is a monkey patch to robot version 2.5 settings.

This should be removed when next version of Robot is released.
'''

from robot.parsing.settings import Timeout, _Setting, Fixture, Template, Metadata
from robotide.context import SETTINGS


def _setting_data_as_list(self):
    ret = [self.setting_name]
    if self.value:
        ret.extend(self.value)
    return ret

def _timeout_data_as_list(self):
    ret = [self.setting_name]
    if self.value or self.message:
        ret.append(self.value if self.value else '')
    if self.message:
        ret.append(self.message)
    return ret

def _fixture_data_as_list(self):
    ret = [self.setting_name]
    if self.name or self.args:
        ret.append(self.name if self.name else '')
    if self.args:
        ret.extend(self.args)
    return ret

def _template_data_as_list(self):
    ret = [self.setting_name]
    if self.value:
        ret.append(self.value)
    return ret

def _metadata_data_as_list(self):
    if SETTINGS['metadata style'].lower() == 'old':
        return ['Meta: %s' % self.name, self.value]
    return [self.setting_name, self.name, self.value]


_Setting._data_as_list = _setting_data_as_list
Timeout._data_as_list = _timeout_data_as_list
Fixture._data_as_list = _fixture_data_as_list
Template._data_as_list = _template_data_as_list
Metadata._data_as_list = _metadata_data_as_list
