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

# Have to use short options in some methods, because of long option was changed
# in RF 2.8 -> 2.9, and we don't necessarily know the installed version.


class CommandArgs:
    def __init__(self):
        self._existing_args = []
        self._args = []
        self._without_console_color = False
        self._tests_to_run = []
        self._python_paths = []
        self._console_width = ''
        self._output_directory = ''
        self._log_level = ''

    def with_existing_args(self, args):
        self._existing_args = args
        return self

    def with_python_path(self, paths):
        self._python_paths = paths
        return self

    def with_log_level(self, log_level):
        self._log_level = log_level
        return self

    def with_output_directory(self, output_directory):
        self._output_directory = output_directory
        return self

    def with_runnable_tests(self, tests):
        self._tests_to_run.clear()
        for suite, test in tests:
            self._tests_to_run += ['--suite', suite, '--test', test]
        return self

    def without_console_color(self, without_colors=True):
        self._without_console_color = without_colors
        return self

    def with_console_width(self, console_width):
        self._console_width = console_width
        return self

    def build(self):
        if self._existing_args:
            self._args.extend(self._existing_args)

        if self._is_necessary_disable_console_color():
            self._args.extend(['-C', 'off'])

        if self._is_necessary_add_console_color():
            from sys import platform
            if platform.endswith('win32'):
                self._args.extend(['-C', 'ansi'])
            else:
                self._args.extend(['-C', 'on'])

        if self._is_necessary_add_console_width():
            self._args.extend(['-W', self._console_width])

        if self._is_necessary_add_python_paths():
            self._args.extend(
                ['-P', ':'.join(self._python_paths)])

        if self._is_necessary_add_output_dir():
            self._args.extend(['-d', self._output_directory])

        if self._is_necessary_add_log_level():
            self._args.extend(['-L', self._log_level])

        self._args.extend(self._tests_to_run)

        return self._args

    def _is_necessary_disable_console_color(self):
        return self._without_console_color and \
               '-C' not in self._args and \
               '--consolecolors' not in self._args

    def _is_necessary_add_console_color(self):
        return not self._without_console_color and \
               '-C' not in self._args and \
               '--consolecolors' not in self._args

    def _is_necessary_add_console_width(self):
        return self._console_width and \
               '-W' not in self._args and \
               '--consolewidth' not in self._args

    def _is_necessary_add_python_paths(self):
        return self._python_paths and \
               '-P' not in self._args and \
               '--pythonpath' not in self._args

    def _is_necessary_add_output_dir(self):
        return self._output_directory and \
               '-d' not in self._args and \
               '--outputdir' not in self._args

    def _is_necessary_add_log_level(self):
        return self._log_level and \
               '-L' not in self._args and \
               '--loglevel' not in self._args
