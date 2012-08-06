import unittest
from robotide.contrib.testrunner.testrunnerplugin import Process

class ProcessUnicodeTestCase(unittest.TestCase):

    def test_unicode_command(self):
        p = Process(u'\xf6')
        try:
            p.run_command(u'\xf6')
        except OSError, expected:
            pass
        except UnicodeEncodeError:
            self.fail('Should not throw unicode error')


if __name__ == '__main__':
    unittest.main()
