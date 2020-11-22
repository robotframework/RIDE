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


class CommandArgsBuilder:

    def __init__(self):
        self._existing_args = []
        self._standard_args = []
        self._without_console_color_args = []
        self._tests_to_run_args = []
        self._python_path_arg = ''
        self._console_width_arg = ''
        self._output_dir_arg = ''
        self._log_level = ''

    def __init__(self, existing_args):
        self._existing_args = existing_args
        self._standard_args = []
        self._without_console_color_args = []
        self._tests_to_run_args = []
        self._python_path_arg = ''
        self._console_width_arg = ''
        self._output_dir_arg = ''
        self._log_level = ''

    def without_console_color(self):
        self._without_console_color_args = ['-C', 'off']

    def set_tests_to_run(self, tests_to_run):
        self._tests_to_run_args.clear()
        for suite, test in tests_to_run:
            self._tests_to_run_args += ['--suite', suite, '--test', test]

    def set_python_path(self, python_path):
        self._python_path_arg = python_path

    def set_console_width(self, console_width):
        self._console_width_arg = console_width

    def set_output_directory(self, output_directory):
        self._output_dir_arg = output_directory

    def set_log_level(self, log_level):
        self._log_level = log_level

    def build(self):
        if self._existing_args:
            self._standard_args.extend(self._existing_args)

        if self._without_console_color_args:
            self._standard_args.extend(self._without_console_color_args)

        if self._is_necessary_add_console_width():
            self._standard_args.extend(['-W', self._console_width_arg])

        if self._is_necessary_add_python_path():
            self._standard_args.extend(['-P', ':'.join(self._python_path_arg)])

        if self._is_necessary_add_output_dir():
            self._standard_args.extend(['-d', self._output_dir_arg])

        if self._is_necessary_add_log_level():
            self._standard_args.extend(['-L', self._log_level])

        self._standard_args.extend(self._tests_to_run_args)

        return self._standard_args

    def _is_necessary_add_console_width(self):
        return self._console_width_arg and \
               '-W' not in self._standard_args and \
               '--consolewidth' not in self._standard_args

    def _is_necessary_add_python_path(self):
        return self._python_path_arg and \
               '-P' not in self._standard_args and \
               '--pythonpath' not in self._standard_args

    def _is_necessary_add_output_dir(self):
        return self._output_dir_arg and \
               '-d' not in self._standard_args and \
               '--outputdir' not in self._standard_args

    def _is_necessary_add_log_level(self):
        return self._log_level and \
               '-L' not in self._standard_args and \
               '--loglevel' not in self._standard_args
