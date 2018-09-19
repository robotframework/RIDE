import unittest
import robotide.lib.robot.errors
from robotide.contrib.testrunner.runprofiles import PybotProfile


class TestPybotArgumentsValidation(unittest.TestCase):

    def setUp(self):
        self._profile = PybotProfile(lambda:0)

    @unittest.expectedFailure   # No more DataError, better argument detection
    def test_invalid_argument(self):
        try:
            self.assertRaisesRegex(robotide.lib.robot.errors.DataError,
                                   'option --invalidargument not recognized',
                                   self._profile._get_invalid_message,
                                   '--invalidargument')
        except AttributeError:  # Python2
            self.assertRaisesRegexp(robotide.lib.robot.errors.DataError,
                                    'option --invalidargument not recognized',
                                    self._profile._get_invalid_message,
                                    '--invalidargument')

    def test_valid_argument_short(self):
        self._working_arguments('-T')

    def _working_arguments(self, args):
        self.assertEqual(None, self._profile._get_invalid_message(args))

    def test_valid_argument_long(self):
        self._working_arguments('--timestampoutputs')

    def test_valid_argument_with_value(self):
        self._working_arguments('--log somelog.html')

    def test_runfailed_argument_works(self):
        self._working_arguments('--runfailed output.xml')


if __name__ == '__main__':
    unittest.main()
