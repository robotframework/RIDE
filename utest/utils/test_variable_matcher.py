import unittest
from robotide import utils
from robot.utils.asserts import assert_equals

class TestVariableMatcher(unittest.TestCase):

    def test_find_variables(self):
        assert_equals(utils.find_variable_basenames('hu ${huhu + 5} pupu ${foo} uhhu ${gugy.gug sdknjs +enedb} {{]{}{}{[[}'),
                                                ['huhu ', 'foo', 'gugy'])


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()