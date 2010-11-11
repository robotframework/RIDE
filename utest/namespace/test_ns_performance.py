import time
import unittest

from robot.utils.asserts import assert_true
from robotide.namespace import Namespace
from robotide.controller.chiefcontroller import ChiefController

from resources import MessageRecordingLoadObserver
from datafilereader import TESTCASEFILE_WITH_EVERYTHING

class TestNamespacePerformance(unittest.TestCase):

    def test_user_keyword_find_performance(self):
        self._execute_keyword_find_function_n_times('is_user_keyword', 5000)

    def test_library_keyword_find_performance(self):
        self._execute_keyword_find_function_n_times('is_library_keyword', 5000)

    def _execute_keyword_find_function_n_times(self, function, n):
        ns = Namespace()
        chief = ChiefController(ns)
        chief.load_datafile(TESTCASEFILE_WITH_EVERYTHING,
                            MessageRecordingLoadObserver())
        everything_tcf = chief._controller.data
        start_time = time.time()
        for i in range(n):
            func = getattr(ns, function)
            func(everything_tcf, 'hevonen %s' % i)
        end_time = time.time() - start_time
        assert_true(end_time < 0.5, 'Checking %d kws took too long: %fs.' % (n, end_time))
