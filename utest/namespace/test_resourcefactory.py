import os
import unittest
from robot.parsing.settings import _Import
from robotide.namespace.resourcefactory import ResourceFactory


class _ResourceFactory(ResourceFactory):

    def _get_resource(self, path):
        return object()


class ResourceFactoryDirectoryIgnoreTestCase(unittest.TestCase):

    def setUp(self):
        self._import = _Import(None, __file__)
        self._context = self._mock_context()

    def test_resourcefactory_finds_imported_resource(self):
        self._is_resolved(_ResourceFactory())

    def test_resourcefactory_ignores_imported_resource_from_ignore_directory(self):
        r = _ResourceFactory(exclude_directory=os.path.dirname(__file__))
        self.assertEqual(None, r.get_resource_from_import(self._import, self._context))

    def test_resourcefactory_ignores_imported_resource_from_ignore_subdirectory(self):
        r = _ResourceFactory(exclude_directory=os.path.split(os.path.dirname(__file__))[0])
        self.assertEqual(None, r.get_resource_from_import(self._import, self._context))

    def test_resourcefactory_finds_imported_resource_when_subdirectory_ignored(self):
        r = _ResourceFactory(exclude_directory=os.path.join(os.path.dirname(__file__), 'something'))
        self._is_resolved(r)

    def test_resourcefactory_finds_imported_resource_when_similar_ignore_name(self):
        r = _ResourceFactory(exclude_directory=os.path.dirname(__file__))
        imp = _Import(None, os.path.join(os.path.dirname(__file__)+'2', 'foo'))
        self._is_resolved(r, imp)

    def test_resourcefactory_ignores_imported_resource_when_relative_import(self):
        r = _ResourceFactory(exclude_directory=os.path.abspath('.'))
        imp = _Import(None, os.path.join('.', 'foo'))
        self.assertEqual(None, r.get_resource_from_import(imp, self._context))

    def _mock_context(self):
        context = lambda:0
        context.vars = context
        context.replace_variables = lambda s: s
        return context

    def _is_resolved(self, factory, imp=None):
        imp = imp or self._import
        self.assertNotEqual(None, factory.get_resource_from_import(imp, self._context))


if __name__ == '__main__':
    unittest.main()
