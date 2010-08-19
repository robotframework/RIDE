import unittest
from robotide.mac_localization import only_once
from robot.utils.asserts import assert_true, assert_false


class EventMock(object):

    def __init__(self, id):
        self.Id = id


class TestMacFix(unittest.TestCase):

    @only_once
    def _example(self, arg):
        return True

    def test_run_only_once(self):
        event1 = EventMock(1)
        event2 = EventMock(2)
        assert_true(self._example(event1))
        assert_false(self._example(event1))
        assert_true(self._example(event2))