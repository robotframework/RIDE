import unittest
from robotide.controller.filecontrollers import ResourceFileControllerFactory


class ResourceFileControllerFactoryTestCase(unittest.TestCase):

    def setUp(self):
        namespace = lambda:0
        project = lambda:0
        self._resource_file_controller_factory = ResourceFileControllerFactory(namespace, project)

    def test_is_all_resource_imports_resolved(self):
        self.assertFalse(self._resource_file_controller_factory.is_all_resource_file_imports_resolved())
        self._resource_file_controller_factory.set_all_resource_imports_resolved()
        self.assertTrue(self._resource_file_controller_factory.is_all_resource_file_imports_resolved())
        self._resource_file_controller_factory.set_all_resource_imports_unresolved()
        self.assertFalse(self._resource_file_controller_factory.is_all_resource_file_imports_resolved())

    def test_all_resource_imports_is_unresolved_when_new_resource_is_added(self):
        self._resource_file_controller_factory.set_all_resource_imports_resolved()
        data = lambda:0
        data.source = 'source'
        data.directory = 'directory'
        self._resource_file_controller_factory.create(data)
        self.assertFalse(self._resource_file_controller_factory.is_all_resource_file_imports_resolved())

    def test_all_resource_imports_is_unresolved_when_new_resource_is_added(self):
        self._resource_file_controller_factory.set_all_resource_imports_resolved()
        resu = lambda:0
        self._resource_file_controller_factory._resources.append(resu)
        self._resource_file_controller_factory.remove(resu)
        self.assertFalse(self._resource_file_controller_factory.is_all_resource_file_imports_resolved())


if __name__ == '__main__':
    unittest.main()
