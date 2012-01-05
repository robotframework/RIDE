#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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

from robot.running.userkeyword import EmbeddedArgsTemplate


class EmbeddedArgsHandler(EmbeddedArgsTemplate):

    def __init__(self, keyword):
        if keyword.arguments:
            raise TypeError('Cannot have normal arguments')
        self.embedded_args, self.name_regexp \
                = self._read_embedded_args_and_regexp(keyword.name)
        if not self.embedded_args:
            raise TypeError('Must have embedded arguments')
