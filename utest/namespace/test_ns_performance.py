import os
import time
import unittest

from robot.utils.asserts import assert_true
from robotide.namespace import Namespace
from robotide.controller.chiefcontroller import ChiefController



DATAPATH = os.path.join(os.path.abspath(os.path.split(__file__)[0]),
                        '..', 'resources', 'robotdata')
TESTCASEFILE_WITH_EVERYTHING = os.path.normpath(os.path.join(DATAPATH, 'testsuite',
                                                   'everything.html'))

class TestNamespacePerformance(unittest.TestCase):
    def test_keyword_find_performance(self):
        ns = Namespace()
        chief = ChiefController(ns, None)
        chief.load_datafile(TESTCASEFILE_WITH_EVERYTHING)
        everything_tcf = chief._controller.data
        start_time = time.time()
        for i in range(100):
            ns.is_user_keyword(everything_tcf, 'hevonen %s' % i)
        end_time = time.time() - start_time
        assert_true(end_time < 0.5, 'Checking 100 kws took too long: %fs.' % end_time)
