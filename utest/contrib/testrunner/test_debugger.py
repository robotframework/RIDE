from contextlib import contextmanager
import threading
import unittest
import time
from robotide.contrib.testrunner.TestRunnerAgent import RobotDebugger

class TestDebugger(unittest.TestCase):

    def setUp(self):
        self._debugger = RobotDebugger()

    def test_pausing_and_resuming(self):
        self.assertFalse(self._debugger.is_paused())
        self._debugger.pause()
        self.assertTrue(self._debugger.is_paused())
        self._debugger.resume()
        self.assertFalse(self._debugger.is_paused())

    def test_is_breakpoint(self):
        self.assertTrue(self._debugger.is_breakpoint('BuiltIn.Comment', {'args':['PAUSE']}))
        self.assertFalse(self._debugger.is_breakpoint('BuiltIn.Log', {'args':['PAUSE']}))
        self.assertFalse(self._debugger.is_breakpoint('BuiltIn.Comment', {'args':['Something']}))
        self.assertFalse(self._debugger.is_breakpoint('Foo', {'args':[]}))

    def test_step_next(self):
        self._debugger.pause()
        started = threading.Event()
        first_keyword_done = threading.Event()
        second_keyword_done = threading.Event()
        third_keyword_done = threading.Event()
        wait_for_step_next_before_entering_debugger = threading.Event()

        def test_execution():
            started.set()
            with self.kw():
                first_keyword_done.set()
                wait_for_step_next_before_entering_debugger.wait()
                with self.kw():
                    second_keyword_done.set()
            with self.kw():
                third_keyword_done.set()

        with self.execution(test_execution):
            self._verify_done(started)
            self.assertFalse(first_keyword_done.isSet())
            self._debugger.step_next()
            self._verify_done(first_keyword_done)
            self.assertFalse(second_keyword_done.isSet())
            self._debugger.step_next()
            wait_for_step_next_before_entering_debugger.set()
            self._verify_done(second_keyword_done)
            self.assertFalse(third_keyword_done.isSet())
            self._debugger.step_next()
            self._verify_done(third_keyword_done)


    def _verify_done(self, event):
        self.assertTrue(event.wait(timeout=10.0) or event.isSet())

    @contextmanager
    def kw(self, passes=True):
        self._debugger.start_keyword()
        yield
        self._debugger.end_keyword(passes)

    @contextmanager
    def execution(self, executed):
        t = threading.Thread(target=executed)
        t.setDaemon(True)
        t.start()
        yield
        t.join()

    def test_step_over(self):
        self._debugger.pause()
        started = threading.Event()
        first_keyword_done = threading.Event()
        second_keyword_done = threading.Event()
        third_keyword_done = threading.Event()
        last_keyword_done = threading.Event()

        def test_execution():
            started.set()
            with self.kw():
                first_keyword_done.set()
                with self.kw():
                    with self.kw():
                        pass
                    with self.kw():
                        pass
                    second_keyword_done.set()
                with self.kw():
                    third_keyword_done.set()
            with self.kw():
                last_keyword_done.set()

        with self.execution(test_execution):
            self._verify_done(started)
            self.assertFalse(first_keyword_done.isSet())
            self._debugger.step_next()
            self._verify_done(first_keyword_done)
            self.assertFalse(second_keyword_done.isSet())
            self._debugger.step_over()
            self._verify_done(second_keyword_done)
            self.assertFalse(third_keyword_done.isSet())
            self._debugger.step_over()
            self._verify_done(third_keyword_done)
            self.assertFalse(last_keyword_done.isSet())
            self._debugger.step_over()
            self._verify_done(last_keyword_done)

    def test_pause_on_failure(self):
        self._debugger.pause_on_failure(True)
        before_failure = threading.Event()
        after_failure = threading.Event()

        def test_execution():
            with self.kw():
                pass
            with self.kw():
                pass
            before_failure.set()
            with self.kw(False):
                pass
            with self.kw():
                pass
            after_failure.set()

        with self.execution(test_execution):
            self._verify_done(before_failure)
            self.assertFalse(after_failure.isSet())
            self._debugger.resume()
            time.sleep(0)
            self._verify_done(after_failure)

if __name__ == '__main__':
    unittest.main()
