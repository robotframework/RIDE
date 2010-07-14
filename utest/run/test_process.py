import unittest
import os
import sys
import time

from robotide.run.process import Process
from robot.utils.asserts import assert_equals, assert_false, assert_true, \
        assert_raises_with_msg


SCRIPT = os.path.join(os.path.dirname(__file__), 
                      'process_test_scripts.py').replace(' ', '<SPACE>')


class TestProcess(unittest.TestCase):

        # FIXME: Is this test needed? Should it work on windows?
    if os.name != 'nt':
        def test_start(self):
            self.proc = self._create_process(['echo', 'test test'])
            self._wait_until_finished()
            self._assert_output('test test\n')

    def test_command_as_string(self):
        cmd = 'python %s count_args a1 a2<SPACE>2<SPACE>1 a3<SPACE>' % SCRIPT
        self.proc = self._create_process(cmd)
        self._wait_until_finished()
        self._assert_output('3\n')

    if sys.version_info[:2] >= (2,6):
        def test_stopping(self):
            self.proc = self._create_process('python %s output 0.8' % SCRIPT)
            time.sleep(0.5)
            self.proc.stop()
            time.sleep(0.5)
            assert_true(self.proc.get_output().startswith('start\nrunning '))
            assert_false(os.path.exists(self.proc._out_path))
            assert_true(self.proc.is_finished())

    else:
        def test_stopping(self):
            msg = 'Stopping process is possible only with Python 2.6 or newer'
            assert_raises_with_msg(AttributeError, msg,
                                   self._create_process(['']).stop)

    def test_error(self):
        proc = self._create_process(['invalid command'])
        assert_true(proc.get_output() is not None)
        assert_true(proc.is_finished())

    def test_output(self):
        self.proc = self._create_process('python %s output' % SCRIPT)
        time.sleep(0.2)
        length = len(self.proc.get_output())
        assert_true(length > 0)
        self._wait_until_finished()
        output = self.proc.get_output()
        assert_true(len(output) > length)
        assert_true(output.endswith('done\n'))

    def test_writing_to_stderr(self):
        self.proc = self._create_process('python %s stderr' % SCRIPT)
        assert_equals(self.proc.get_output(wait_until_finished=True),
                      'This is stderr\n')

    def _create_process(self, command):
        proc = Process(command)
        proc.start()
        return proc

    def _assert_output(self, output):
        assert_equals(self.proc.get_output(), output)
        assert_true(self.proc.is_finished())

    def _wait_until_finished(self):
        while not self.proc.is_finished():
            time.sleep(0.1)

