import os
import unittest

from robotide.controller.chiefcontroller import ChiefController
from robotide.namespace.namespace import Namespace
from resources import MINIMAL_SUITE_PATH, SUITEPATH
from robot.utils.asserts import assert_not_none, assert_true, assert_false


class TestFormatChange(unittest.TestCase):

    def test_format_change(self):
        controller = self._get_file_controller(MINIMAL_SUITE_PATH)
        assert_not_none(controller)
        controller.save_with_new_format('tsv')
        self._assert_removed(MINIMAL_SUITE_PATH)
        path_with_tsv = os.path.splitext(MINIMAL_SUITE_PATH)[0] + '.tsv'
        self._assert_serialized(path_with_tsv)

    def test_recursive_format_change(self):
        controller = self._get_file_controller(SUITEPATH)
        controller.save_with_new_format_recursive('txt')
        init_file = os.path.join(SUITEPATH,'__init__.txt')
        self._assert_serialized(init_file)
        path_to_sub_init_file = os.path.join(SUITEPATH,'subsuite','__init__.txt')
        self._assert_serialized(path_to_sub_init_file)
        path_to_old_sub_init_file = os.path.join(SUITEPATH,'subsuite','__init__.tsv')
        self._assert_removed(path_to_old_sub_init_file)
        path_to_txt_file = os.path.join(SUITEPATH,'subsuite','test.txt')
        self._assert_not_serialized(path_to_txt_file)
        self._assert_not_removed(path_to_txt_file)

    def setUp(self):
        ns = Namespace()
        self.chief = ChiefControllerChecker(ns)

    def _get_file_controller(self, path):
        self.chief.load_datafile(path)
        return self.chief._controller

    def _assert_serialized(self, path):
        assert_true(path in self.chief.serialized_files)

    def _assert_not_serialized(self, path):
        assert_false(path in self.chief.serialized_files)

    def _assert_removed(self, path):
        assert_true(path in self.chief.removed_files)

    def _assert_not_removed(self, path):
        assert_false(path in self.chief.removed_files)


class ChiefControllerChecker(ChiefController):

    def __init__(self, namespace):
        self.removed_files = []
        self.serialized_files = []
        ChiefController.__init__(self, namespace)

    def serialize_controller(self, controller):
        self.serialized_files.append(controller.source)

    def _remove_file(self, path):
        self.removed_files.append(path)


if __name__ == "__main__":
    unittest.main()
