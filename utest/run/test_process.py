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

import unittest
import os

import pytest

from robotide.context import IS_WINDOWS
from robotide.run.process import Process

SCRIPT = os.path.join(os.path.dirname(__file__),
                      'process_test_scripts.py').replace(' ', '<SPACE>')


class TestProcess(unittest.TestCase):

    def test_command_as_string(self):
        initial_command = 'python hupu count_args a1 a2<SPACE>2<SPACE>1 a3<SPACE>'
        processed_command = Process(initial_command)._command
        assert len(processed_command) == len(initial_command.split())
        assert processed_command[4] == 'a2 2 1'

    @pytest.mark.skipif(os.getenv('GITHUB_ACTIONS')=='true', reason="Fails at Fedora workflow")
    def test_writing_to_stderr(self):
        self.proc = self._create_process('python %s stderr' % SCRIPT)
        eol = '\r\n' if IS_WINDOWS else '\n'
        assert (self.proc.get_output(wait_until_finished=True) == bytes(f"This is stderr{eol}", encoding='utf-8'))

    @staticmethod
    def _create_process(command):
        proc = Process(command)
        proc.start()
        return proc


if __name__ == '__main__':
    unittest.main()
