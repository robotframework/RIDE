import unittest
from robot.utils.asserts import assert_true

from robotide.application.chiefcontroller import ChiefController
from robotide.namespace import Namespace

from resources import MINIMAL_SUITE_PATH, RESOURCE_PATH


class _FakeObserver(object):

    def notify(self):
        pass

    def finished(self):
        self.finished = True

class Test(unittest.TestCase):

    def test_loading_suite(self):
        chief = ChiefController(Namespace())
        obs = _FakeObserver()
        chief.load_data(obs, MINIMAL_SUITE_PATH)
        assert_true(obs.finished)
        assert_true(chief._controller is not None)

    def test_loading_resource(self):
        chief = ChiefController(Namespace())
        obs = _FakeObserver()
        chief.load_data(obs, RESOURCE_PATH)
        assert_true(obs.finished)
        assert_true(chief.resources != [])


if __name__ == "__main__":
    unittest.main()
