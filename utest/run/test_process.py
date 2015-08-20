import unittest
import os

from robotide.run.process import Process
from nose.tools import assert_equals


SCRIPT = os.path.join(os.path.dirname(__file__),
                      'process_test_scripts.py').replace(' ', '<SPACE>')


class TestProcess(unittest.TestCase):

    def test_command_as_string(self):
        initial_command = 'python hupu count_args a1 a2<SPACE>2<SPACE>1 a3<SPACE>'
        processed_command = Process(initial_command)._command
        assert_equals(len(processed_command), len(initial_command.split()))
        assert_equals(processed_command[4], 'a2 2 1')

    def test_writing_to_stderr(self):
        self.proc = self._create_process('python %s stderr' % SCRIPT)
        assert_equals(self.proc.get_output(wait_until_finished=True),
                      'This is stderr\n')

    def _create_process(self, command):
        proc = Process(command)
        proc.start()
        return proc
