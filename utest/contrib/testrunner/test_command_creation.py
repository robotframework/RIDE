import os
import unittest

from robotide.robotapi import LOG_LEVELS as LEVELS
from robotide.contrib.testrunner.testrunner import TestRunner


class CommandCreator(TestRunner):

    def _get_listener_to_cmd(self):
        return 'listener'

    def _write_argfile(self, argfile, args):
        self.arguments = args

class CommandCreationTestCase(unittest.TestCase):

    def test_command(self):
        fakeproject = lambda:0
        fakeproject.suite = lambda:0
        fakeproject.suite.source = 'source'
        creator = CommandCreator(fakeproject)
        creator._output_dir = 'temppi'
        command = creator.get_command(self._create_profile(), ['PYTHON', 'PATH'], 7, [('suite', 'suite.test')])
        self.assertEqual(command,
            ['prefix', '--argumentfile', os.path.join('temppi','argfile.txt'),
             '--listener', 'listener', os.path.abspath('source')])
        self.assertEqual(creator.arguments,
            ['custom', 'args',
             '--outputdir', 'temppi',
             '--pythonpath', 'PYTHON:PATH',
             '-C', 'off', # --consolecolors
             '-W', 7, # --consolewidth
             '--suite', 'suite',
             '--test', 'suite.test'])

    def _create_profile(self):
        p = lambda:0
        p.get_command_prefix = lambda: ['prefix']
        p.get_custom_args = lambda: ['custom', 'args']
        return p

    def test_min_log_level_settings(self):
        self._min_log_level_setting_test(['-L', 'warn'], 'WARN')
        self._min_log_level_setting_test(['--loglevel', 'debug'], 'DEBUG')
        self._min_log_level_setting_test(['prefix'], 'INFO')
        self._min_log_level_setting_test(['-L', 'obscure'], 'INFO')
        self._min_log_level_setting_test(['--loglevel', 'WARN:TRACE'], 'WARN')


    def _min_log_level_setting_test(self, command_as_list, expected_level):
        creator = CommandCreator(None)
        self.assertEquals(creator.get_message_log_level(command_as_list), LEVELS[expected_level])


if __name__ == '__main__':
    unittest.main()
