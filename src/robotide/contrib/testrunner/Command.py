# Copyright 2010 Orbitz WorldWide
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Modified by NSN
#  Copyright 2010-2012 Nokia Solutions and Networks
#  Copyright 2013-2015 Nokia Networks
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

import inspect
import os

from robotide.contrib.testrunner import TestRunnerAgent
try:
    from robotide.lib.robot.utils import encoding
except ImportError:
    from robotide.lib.robot.utils.encodingsniffer import get_system_encoding
    encoding.SYSTEM_ENCODING = get_system_encoding()


class Command:
    def __init__(self):
        self._prefix = ''
        self._tests_suite_file = ''
        self._listener = None
        self._args_file = ''

    def with_prefix(self, prefix):
        self._prefix = prefix
        return self

    def with_listener(self, port, pause_on_failure=False):
        if port:
            self._listener = (port, pause_on_failure)
        else:
            self._listener = None
        return self

    def with_tests_suite_file(self, tests_suit_file):
        self._tests_suite_file = tests_suit_file
        return self

    def with_args_file(self, args_file):
        self._args_file = args_file
        return self

    def build(self):
        command = []
        if self._prefix:
            command.append(self._prefix)

        if self._args_file:
            command.extend(["-A", self._args_file])

        if self._listener:
            command.extend(["--listener", self._get_listener_to_cmd()])

        if self._tests_suite_file:
            command.append(self._tests_suite_file)

        return self._format_command(command)

    def _get_listener_to_cmd(self):
        path = self._get_listener_path()
        if path[-1] in ['c', 'o']:
            path = path[:-1]
        return '%s:%s:%s' % (path, self._listener[0], self._listener[1])

    def _get_listener_path(self):
        return os.path.abspath(inspect.getfile(TestRunnerAgent))

    @staticmethod
    def _format_command(args):
        """Quote a list as if it were a command line command

        This isn't perfect but seems to work for the normal use
        cases. I'm not entirely sure what the perfect algorithm
        is since *nix and windows have different quoting
        behaviors.
        """
        result = []
        for arg in args:
            if "'" in arg or " " in arg or "&" in arg:
                # for windows, if there are spaces we need to use
                # double quotes. Single quotes cause problems
                result.append('"%s"' % arg)
            elif '"' in arg:
                result.append("'%s'" % arg)
            else:
                result.append(arg)
        return " ".join(result)
