#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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

import re

from robotide.robotapi import VariableSplitter


class EmbeddedArgsHandler(object):

    def __init__(self, keyword):
        if keyword.arguments:
            raise TypeError('Cannot have normal arguments')
        self.embedded_args, self.name_regexp \
                = self._read_embedded_args_and_regexp(keyword.name)
        if not self.embedded_args:
            raise TypeError('Must have embedded arguments')

    def _read_embedded_args_and_regexp(self, string):
        args = []
        regexp = ['^']
        while True:
            before, variable, rest = self._split_from_variable(string)
            if before is None:
                break
            args.append(variable)
            regexp.extend([re.escape(before), '(.*?)'])
            string = rest
        regexp.extend([re.escape(rest), '$'])
        return args, re.compile(''.join(regexp), re.IGNORECASE)

    def _split_from_variable(self, string):
        var = VariableSplitter(string, identifiers=['$'])
        if var.identifier is None:
            return None, None, string
        return string[:var.start], string[var.start:var.end], string[var.end:]
