import os
import unittest
from robot.parsing.model import TestCaseFile, ResourceFile
from robotide.controller import ResourceFileController

from robotide.controller.chiefcontroller import ChiefController
from robotide.controller.filecontrollers import TestCaseFileController
from robotide.namespace.namespace import Namespace
from robot.utils.asserts import assert_not_none, assert_true, assert_false, assert_equals, assert_none

from resources import MINIMAL_SUITE_PATH, SUITEPATH, MessageRecordingLoadObserver


class TestFormatChange(unittest.TestCase):

    def setUp(self):
        ns = Namespace()
        self.chief = ChiefControllerChecker(ns)

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

    def _get_file_controller(self, path):
        self.chief.load_datafile(path, MessageRecordingLoadObserver())
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


class TestResourceFormatChange(unittest.TestCase):

    def test_imports_are_updated(self):
        self._create_data('name.txt', 'name.txt')
        self._change_format('BAR')
        self._assert_format_change('name.bar', 'name.bar')

    def test_imports_with_variables_and_path_are_updated(self):
        self._create_data('name.txt', '${dirname}/name.txt')
        self._change_format('cock')
        self._assert_format_change('${dirname}/name.cock', 'name.cock')

    def test_imports_with_only_variables(self):
        self._create_data('res.txt', '${path}')
        self._change_format('zap')
        self._assert_format_change('${path}', 'res.zap', imp_is_resolved=False)

    def _create_data(self, resource_name, resource_import):
        res_path = os.path.abspath(resource_name)
        tcf = TestCaseFile(source=os.path.abspath('test.txt'))
        tcf.setting_table.add_resource(resource_import)
        tcf.variable_table.add('${dirname}', os.path.abspath('.'))
        tcf.variable_table.add('${path}', os.path.abspath(resource_name))
        self.chef = ChiefController(namespace=Namespace())
        self.chef._controller = TestCaseFileController(tcf, self.chef)
        res = ResourceFile(source=res_path)
        self.res_controller = \
            self.chef._resource_file_controller_factory.create(res, self.chef)
        self.chef._namespace._resource_factory.cache[res_path] = res

    def _change_format(self, format):
        self.res_controller.set_format(format)

    def _assert_format_change(self, import_name, resource_path,
                              imp_is_resolved=True):
        imp = self.chef._controller.imports[0]
        assert_equals(imp.name, import_name)
        assert_equals(self.res_controller.filename, os.path.abspath(resource_path))
        if imp_is_resolved:
            assert_equals(imp.get_imported_controller(),
                          self.res_controller)
        else:
            assert_none(imp.get_imported_controller())


if __name__ == "__main__":
    unittest.main()
