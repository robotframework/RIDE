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
import time
import os
import pytest
from robotide.run.runanything import RunConfig
from robotide.run.ui import Runner
from utest.resources import UIUnitTestBase
DISPLAY = os.getenv('DISPLAY')
# if not DISPLAY:
#     pytest.skip("Skipped because of missing DISPLAY", allow_module_level=True)  # Avoid failing unit tests without X11


SCRIPT = os.path.join(os.path.dirname(__file__),
                      'process_test_scripts.py').replace(' ', '<SPACE>')


class _TestableRunner(Runner):
    output = property(lambda self: self._window.output)
    outstr = property(lambda self: self._window.outstr)
    finished = property(lambda self: self._window.finished)

    def _get_output_window(self, notebook):
        return _FakeOutputWindow()


class _FakeOutputWindow(object):
    outstr = property(lambda self: ''.join(self.output))
    output_panel = None

    def __init__(self):
        self.output = []
        self.finished = None

    def update_output(self, output, finished):
        if isinstance(output, bytes):
            output = str(output, encoding='utf-8')
        self.output.append(output)
        self.finished = finished


class TestRunAnything(UIUnitTestBase):

    @pytest.mark.skipif(os.getenv('GITHUB_ACTIONS')=='true', reason="Fails at Fedora workflow")
    def test_run(self):
        self.runner = self._create_runner('python %s count_args a b c' % SCRIPT)
        self._wait_until_finished()
        assert self.runner.finished
        assert self.runner.outstr == f'3{os.linesep}'

    @pytest.mark.skipif(os.getenv('GITHUB_ACTIONS')=='true', reason="Fails at Fedora workflow")
    def test_stopping(self):
        self.runner = self._create_runner('python %s output 0.8' % SCRIPT)
        time.sleep(0.3)
        self.runner.stop()
        self._sleep_and_log_output(0.1)
        assert self.runner.finished
        assert self.runner.outstr == '\nRIDE: ValueError when reading output.\n\n'

    def test_error(self):
        self.runner = self._create_runner('invalid command')
        self._wait_until_finished()
        assert self.runner.finished
        assert self.runner.outstr

    @pytest.mark.skipif(os.getenv('GITHUB_ACTIONS')=='true', reason="Fails at Fedora workflow")
    def test_stderr(self):
        self.runner = self._create_runner('python %s stderr' % SCRIPT)
        self._wait_until_finished()
        assert self.runner.finished
        assert self.runner.outstr == f'This is stderr{os.linesep}'

    @staticmethod
    def _create_runner(cmd):
        runner = _TestableRunner(RunConfig('test', cmd, ''), None)
        runner.run()
        return runner

    def _wait_until_finished(self):
        self.runner._process.wait()
        self.runner.on_timer()

    def _sleep_and_log_output(self, amount):
        time.sleep(amount)
        self.runner.on_timer()


if __name__ == '__main__':
    unittest.main()
