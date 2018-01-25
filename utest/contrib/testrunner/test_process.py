import unittest
import time
import datafilereader

from robotide.contrib.testrunner.testrunner import Process
from robotide.widgets.list import IS_WINDOWS


class ProcessUnicodeTestCase(unittest.TestCase):

    def test_unicode_command(self):
        try:
            Process(u'\xf6').run_command(u'echo \xf6')
        except UnicodeEncodeError:
            self.fail('Should not throw unicode error')
        except OSError as expected:
            pass

    def test_running_robot_test(self):
        output, errors = self._run_small_test()
        self.assertTrue(output.replace('\r','').startswith(
        '==============================================================================\n'
        'Small Test                                                                    \n'
        '==============================================================================\n'
        'Small Test.Test                                                               \n'
        '==============================================================================\n'
        'Passing                                                               | PASS |\n'
        '------------------------------------------------------------------------------\n'
        'Failing                                                               | FAIL |\n'
        'this fails\n'
        '------------------------------------------------------------------------------\n'
        'Small Test.Test                                                       | FAIL |\n'
        '2 critical tests, 1 passed, 1 failed\n2 tests total, 1 passed, 1 failed\n'
        '==============================================================================\n'
        'Small Test                                                            | FAIL |\n'
        '2 critical tests, 1 passed, 1 failed\n2 tests total, 1 passed, 1 failed\n'
        '==============================================================================\n'),
        msg=repr(output))
        self.assertEqual(errors.replace('\r', ''), u'[ WARN ] this passes\n')

    def _run_small_test(self):
        p = Process(datafilereader.SMALL_TEST_PATH)
        p.run_command('robot' + ('.bat' if IS_WINDOWS else '') + ' --output NONE --log NONE --report NONE .')
        max_time = 7.0
        while p.is_alive() and max_time > 0:
            time.sleep(0.1)
            max_time -= 0.1
        if max_time <= 0:
            p.kill()
            raise AssertionError('process did not stop in 7 second time')
        return p.get_output(), p.get_errors()

    def test_stopping_robot_with_listener_should_generate_outputs(self):
        pass

    def test_stopping_robot_with_two_kill_signals_should_not_generate_outputs(self):
        pass

if __name__ == '__main__':
    unittest.main()
