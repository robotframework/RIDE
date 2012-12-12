import unittest
from robotide.controller.filecontrollers import ResourceFileControllerFactory


class ResourceFileControllerFactoryTestCase(unittest.TestCase):

    def test_is_all_resource_imports_resolved(self):
        namespace = lambda:0
        resource_file_controller_factory = ResourceFileControllerFactory(namespace)
        self.assertFalse(resource_file_controller_factory.is_all_resource_file_imports_resolved())
        resource_file_controller_factory.set_all_resource_imports_resolved()
        self.assertTrue(resource_file_controller_factory.is_all_resource_file_imports_resolved())
        resource_file_controller_factory.set_all_resource_imports_unresolved()
        self.assertFalse(resource_file_controller_factory.is_all_resource_file_imports_resolved())

    def test_all_resource_imports_is_unresolved_when_new_resource_is_added(self):
        namespace = lambda:0
        resource_file_controller_factory = ResourceFileControllerFactory(namespace)
        resource_file_controller_factory.set_all_resource_imports_resolved()
        data = lambda:0
        data.source = 'source'
        data.directory = 'directory'
        resource_file_controller_factory.create(data)
        self.assertFalse(resource_file_controller_factory.is_all_resource_file_imports_resolved())

    def test_all_resource_imports_is_unresolved_when_new_resource_is_added(self):
        namespace = lambda:0
        resource_file_controller_factory = ResourceFileControllerFactory(namespace)
        resource_file_controller_factory.set_all_resource_imports_resolved()
        resu = lambda:0
        resource_file_controller_factory._resources.append(resu)
        resource_file_controller_factory.remove(resu)
        self.assertFalse(resource_file_controller_factory.is_all_resource_file_imports_resolved())


if __name__ == '__main__':
    unittest.main()
