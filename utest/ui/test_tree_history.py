import unittest

from nose.tools import assert_equals
from robotide.controller.ui.treecontroller import _History


class TestChange(unittest.TestCase):

    def setUp(self):
        self.history = _History()
        for i in range(4):
            self.history.change(i)

    def test_history_states(self):
        assert_equals(self.history._back, range(4))

    def test_change_ignores_state_if_same_as_previous(self):
        self.history.change(3)
        assert_equals(self.history._back, range(4))

    def test_forward_list_is_kept_when_state_is_ignored(self):
        self.history.back()
        self.history.change(2)
        assert_equals(self.history._forward, [3])

    def test_change_sanity(self):
        self.history.back()
        for _ in range(7):
            self.history.change(2)
        self.history.forward()
        for _ in range(7):
            self.history.change(3)
        self.history.change(4)
        assert_equals(self.history._back, range(5))


class TestBack(unittest.TestCase):

    def setUp(self):
        self.history = _History()
        for i in range(4):
            self.history.change(i)

    def test_back_once(self):
        self._test_back(2)

    def test_back_many(self):
        self._test_back(2, 1)

    def test_back_more_than_states(self):
        self._test_back(2,1,0,0,0)

    def test_back_before_state_change(self):
        assert_equals(_History().back(), None)

    def _test_back(self, *states):
        for state in states:
            assert_equals(self.history.back(), state)


class TestForward(unittest.TestCase):

    def setUp(self):
        self.history = _History()
        for i in range(5):
            self.history.change(i)

    def test_forward_once(self):
        self.history.back()
        self._test_forward(4)

    def test_forward_many(self):
        for _ in range(3):
            self.history.back()
        self._test_forward(2,3,4)

    def test_forward_before_back(self):
        assert_equals(self.history.forward(), None)

    def test_forward_before_state_change(self):
        assert_equals(_History().forward(), None)

    def test_change_between_back_and_forward(self):
        self.history.back()
        self.history.change(42)
        assert_equals(self.history.forward(), None)

    def test_back_forward_back_forward(self):
        assert_equals(self.history.back(), 3)
        assert_equals(self.history.forward(), 4)
        assert_equals(self.history.back(), 3)
        assert_equals(self.history.back(), 2)
        assert_equals(self.history.back(), 1)
        assert_equals(self.history.forward(), 2)
        assert_equals(self.history.forward(), 3)
        assert_equals(self.history.back(), 2)
        assert_equals(self.history.forward(), 3)
        assert_equals(self.history.forward(), 4)

    def _test_forward(self, *states):
        for state in states:
            assert_equals(self.history.forward(), state)

if __name__ == '__main__':
    unittest.main()
