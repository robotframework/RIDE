import threading
import unittest
import time
from robotide.contrib.testrunner.TestRunnerAgent import RobotDebugger

class TestDebugger(unittest.TestCase):

    def test_pausing_and_resuming(self):
        debugger = RobotDebugger()
        self.assertFalse(debugger.is_paused())
        debugger.pause()
        self.assertTrue(debugger.is_paused())
        debugger.resume()
        self.assertFalse(debugger.is_paused())

    def test_step_next(self):
        debugger = RobotDebugger()
        debugger.pause()
        started = threading.Event()
        first_keyword_done = threading.Event()
        second_keyword_done = threading.Event()
        third_keyword_done = threading.Event()
        wait_for_step_next_before_entering_debugger = threading.Event()

        def test_execution():
            started.set()
            debugger.start_keyword()
            first_keyword_done.set()
            wait_for_step_next_before_entering_debugger.wait()
            debugger.start_keyword()
            second_keyword_done.set()
            debugger.end_keyword()
            debugger.end_keyword()
            debugger.start_keyword()
            third_keyword_done.set()
            debugger.end_keyword()

        def debugger_signals():
            self._verify_done(started)
            self.assertFalse(first_keyword_done.isSet())
            debugger.step_next()
            self._verify_done(first_keyword_done)
            self.assertFalse(second_keyword_done.isSet())
            debugger.step_next()
            wait_for_step_next_before_entering_debugger.set()
            self._verify_done(second_keyword_done)
            self.assertFalse(third_keyword_done.isSet())
            debugger.step_next()
            self._verify_done(third_keyword_done)

        t = threading.Thread(target=test_execution)
        t.setDaemon(True)
        t.start()
        debugger_signals()
        t.join()

    def _verify_done(self, event):
        self.assertTrue(event.wait(timeout=1.0) or event.isSet())

if __name__ == '__main__':
    unittest.main()
