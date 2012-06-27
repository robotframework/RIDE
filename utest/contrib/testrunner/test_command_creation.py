import os
import unittest
from robotide.contrib.testrunner.testrunnerplugin import TestRunnerPlugin

class CommandCreator(TestRunnerPlugin):

    def __init__(self):
        self._tmpdir = 'temppi'
        self._tree = lambda:0
        self._tests_to_run = set()
        tc = lambda:0
        tc.longname = 'suite.test'
        self._tests_to_run.add(tc)

    def get_current_profile(self):
        p = lambda:0
        p.get_command_prefix = lambda:['prefix']
        p.get_custom_args = lambda: ['custom', 'args']
        return p

    def _get_listener_to_cmd(self):
        return 'listener'

    def _get_monitor_width(self):
        return 7

    @property
    def model(self):
        m = lambda:0
        m.suite = m
        m.source = 'source'
        return m

    @property
    def global_settings(self):
        return {'pythonpath':['PYTHON','PATH']}

    def _write_argfile(self, argfile, args):
        self._arguments = args

class CommandCreationTestCase(unittest.TestCase):

    def test_command(self):
        creator = CommandCreator()
        command = creator._get_command()
        self.assertEqual(command,
            ['prefix', '--argumentfile', os.path.join('temppi','argfile.txt'),
             '--listener', 'listener', os.path.abspath('source')])
        self.assertEqual(creator._arguments,
            ['custom', 'args',
             '--outputdir', 'temppi',
             '--pythonpath', 'PYTHON:PATH',
             '--monitorcolors', 'off',
             '--monitorwidth', 7,
             '--test', 'suite.test'])

if __name__ == '__main__':
    unittest.main()
