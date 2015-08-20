import time
import unittest

from nose.tools import assert_true
from robotide.namespace import Namespace
from robotide.controller import Project

from resources import MessageRecordingLoadObserver, FakeSettings
from datafilereader import TESTCASEFILE_WITH_EVERYTHING, KW1000_TESTCASEFILE,\
    KW2000_TESTCASEFILE, KW3000_TESTCASEFILE, KW4000_TESTCASEFILE
from robotide.spec.librarymanager import LibraryManager


class TestNamespacePerformance(unittest.TestCase):
    SAFETY_MARGIN = 0.96
    RELEVANT_B_RELATIVE_TO_C = 0.2

    def test_user_keyword_find_performance(self):
        self._test_keyword_find_performance('is_user_keyword')

    def test_library_keyword_find_performance(self):
        self._test_keyword_find_performance('is_library_keyword')

    def _test_keyword_find_performance(self, find_function_name):
        times = 5000
        end_time = self._execute_keyword_find_function_n_times(find_function_name, times)
        assert_true(end_time < 0.5, 'Checking %d kws took too long: %fs.' % (times, end_time))

    def _FLICKERS_measure_user_keyword_find_performance(self):
        times = 1000
        kw1000_result = self._execute_keyword_find_function_n_times('is_user_keyword', times, KW1000_TESTCASEFILE)
        kw2000_result = self._execute_keyword_find_function_n_times('is_user_keyword', times, KW2000_TESTCASEFILE)
        kw3000_result = self._execute_keyword_find_function_n_times('is_user_keyword', times, KW3000_TESTCASEFILE)
        a, b, c = self._calculate_power2_estimate_constants(kw1000_result, kw2000_result, kw3000_result)
        assert_true(b > c or (c <= 0),
                    'Possibly o(n*2) or greater growth in user keyword performance measures!\nkw1000 time = %s kw2000 time = %s kw3000 time = %s'\
                     % (kw1000_result, kw2000_result, kw3000_result))
        if c > 0 and (b <= 0 or c / b > self.RELEVANT_B_RELATIVE_TO_C):
            kw4000_result = self._execute_keyword_find_function_n_times('is_user_keyword', times, KW4000_TESTCASEFILE)
            self._verify_that_power2_estimate_overestimates(a, b, c, kw1000_result, kw2000_result, kw3000_result, kw4000_result)

    def _verify_that_power2_estimate_overestimates(self, a, b, c, kw1000_result, kw2000_result, kw3000_result, kw4000_result):
        def power2estimate(kw_amount):
            x = kw_amount / 1000
            return a + b * x + c * x**2
        assert_true(power2estimate(4000) * self.SAFETY_MARGIN > kw4000_result,
                   'Possibly o(n*2) or greater growth in namespace performance measures!\nkw1000 time = %s kw2000 time = %s kw3000 time = %s kw4000 time = %s'\
                    % (kw1000_result, kw2000_result, kw3000_result, kw4000_result))


    def _calculate_power2_estimate_constants(self, kw1000_result, kw2000_result, kw3000_result):
        # Assume
        # a + b * 1000kw_amount + c * 1000kw_amount**2
        # THE MATH
        # 1 1 1 [a] = kw1000_result
        # 1 2 4 [b] = kw2000_result
        # 1 3 9 [c] = kw3000_result
        # -- reduce [a]
        # 0 1 3 [b] = kw2000_result-kw1000_result
        # 0 2 8 [c] = kw3000_result-kw1000_result
        # -- reduce [b]
        # 0 0 1 [c] = (kw3000_result-kw1000_result-2*(kw2000_result-kw1000_result))/2
        # -- reduce [c]
        # 1 1 0 [a] = kw1000_result - c
        # 0 1 0 [b] = kw2000_result-kw1000_result - 3*c
        # -- reduce [b]
        # a = kw1000_result - c - b
        c = (kw3000_result-kw1000_result-2*(kw2000_result-kw1000_result))/2
        b = kw2000_result-kw1000_result - 3*c
        a = kw1000_result - c - b
        return a, b, c

    def _load(self, testcasefile):
        ns = Namespace(FakeSettings())
        library_manager = LibraryManager(':memory:')
        library_manager.create_database()
        project = Project(ns, settings=ns._settings, library_manager=library_manager)
        project.load_datafile(testcasefile,
                            MessageRecordingLoadObserver())
        return ns, project._controller.data, library_manager

    def _execute_keyword_find_function_n_times(self, function, n, filename=TESTCASEFILE_WITH_EVERYTHING):
        ns, testcasefile, library_manager = self._load(filename)
        try:
            func = getattr(ns, function)
            func(testcasefile, 'hevonen -1') # execute one time to initialize caches correctly
            start_time = time.time()
            for i in range(n):
                func(testcasefile, 'hevonen %s' % i)
            return time.time() - start_time
        finally:
            library_manager.stop()

