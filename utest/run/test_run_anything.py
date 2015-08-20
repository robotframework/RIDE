import unittest
import time
import os
import sys
from nose.tools import assert_equals, assert_true

from robotide.run.runanything import RunConfig
from robotide.run.ui import Runner
from resources import PYAPP_REFERENCE as _


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
    def __init__(self):
        self.output = []
    def update_output(self, output, finished):
        self.output.append(output)
        self.finished = finished


class TestRunAnything(unittest.TestCase):

    def test_run(self):
        self.runner = self._create_runner('python %s count_args a b c' % SCRIPT)
        self._wait_until_finished()
        assert_true(self.runner.finished)
        assert_equals(self.runner.outstr, '3\n')

    if sys.version_info[:2] >= (2,6):
        def test_stopping(self):
            self.runner = self._create_runner('python %s output 0.8' % SCRIPT)
            time.sleep(0.3)
            self.runner.stop()
            self._sleep_and_log_output(0.1)
            assert_true(self.runner.finished)
            assert_true(self.runner.outstr.startswith('start\nrunning '))

    def test_error(self):
        self.runner = self._create_runner('invalid command')
        self._wait_until_finished()
        assert_true(self.runner.finished)
        assert_true(self.runner.outstr)

    def test_stderr(self):
        self.runner = self._create_runner('python %s stderr' % SCRIPT)
        self._wait_until_finished()
        assert_true(self.runner.finished)
        assert_equals(self.runner.outstr, 'This is stderr\n')

    def _create_runner(self, cmd):
        runner = _TestableRunner(RunConfig('test', cmd, ''), None)
        runner.run()
        return runner

    def _wait_until_finished(self):
        self.runner._process.wait()
        self.runner.OnTimer()

    def _sleep_and_log_output(self, amount):
        time.sleep(amount)
        self.runner.OnTimer()
