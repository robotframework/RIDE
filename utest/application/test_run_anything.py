import unittest
import time
import os
from robot.utils.asserts import assert_equals, assert_false, assert_true

from robotide.application.runanything import _Runner, _RunConfig
from resources import PYAPP_REFERENCE


SCRIPT = os.path.join(os.path.dirname(__file__), 'run_test_scripts.py')


class _TestableRunner(_Runner):
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
        config, runner = self._get_config_and_runner('echo test test')
        self._wait_until_finished(config, runner)
        assert_equals(runner.outstr, 'test test\n')
        assert_true(runner.finished)

    def test_stopping(self):
        config, runner  = self._get_config_and_runner('python %s output 0.8' % SCRIPT)
        time.sleep(0.1)
        runner.stop()
        self._sleep_and_log_output(runner, 0.5)
        assert_false(os.path.exists(config._process._out_path))
        assert_true(runner.finished)
        assert_true(runner.outstr.startswith('start\nrunning '))

    def test_error(self):
        config, runner = self._get_config_and_runner('invalid command')
        self._wait_until_finished(config, runner)
        assert_true(runner.outstr)
        assert_true(runner.finished)

    def test_output(self):
        config, runner = self._get_config_and_runner('python %s output' % SCRIPT)
        self._sleep_and_log_output(runner, 0.5)
        length = len(runner.outstr)
        assert_true(length > 0)
        self._wait_until_finished(config, runner)
        assert_true(len(runner.outstr) > length)
        assert_true(runner.outstr.endswith('done\n'))

    def _get_config_and_runner(self, cmd):
        config = _RunConfig('test', cmd, '')
        runner = _TestableRunner(config, None)
        runner.run()
        return config, runner

    def _wait_until_finished(self, config, runner):
        while not config.finished():
            time.sleep(0.1)
        runner.OnTimer()

    def _sleep_and_log_output(self, runner, amount):
        time.sleep(amount)
        runner.OnTimer()

