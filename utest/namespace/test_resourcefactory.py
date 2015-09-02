import os
import unittest
from robotide.robotapi import _Import
from resources import FakeSettings
from robotide.context import IS_WINDOWS
from robotide.namespace.resourcefactory import ResourceFactory


class _ResourceFactory(ResourceFactory):
    from_path = None

    def _load_resource(self, path, report_status):
        return object()

    def _get_python_path(self, name):
        if not self.from_path:
            return None
        return os.path.join(self.from_path, name)

    def _remove(self):
        p = self._excludes._exclude_file_path
        if p:
            os.remove(p)


class ResourceFactoryDirectoryIgnoreTestCase(unittest.TestCase):

    def setUp(self):
        self._import = _Import(None, __file__)
        self._context = self._mock_context()

    def tearDown(self):
        if self.r:
            self.r._remove()

    def test_resourcefactory_finds_imported_resource(self):
        self.r = _ResourceFactory(FakeSettings())
        self._is_resolved(self.r)

    def test_resourcefactory_ignores_imported_resource_from_ignore_directory(self):
        self.r = self._create_factory(os.path.dirname(__file__))
        self.assertEqual(None, self.r.get_resource_from_import(self._import, self._context))

    def test_resourcefactory_ignores_imported_resource_from_ignore_subdirectory(self):
        self.r = self._create_factory(os.path.split(os.path.dirname(__file__))[0])
        self.assertEqual(None, self.r.get_resource_from_import(self._import, self._context))

    def test_resourcefactory_finds_imported_resource_when_subdirectory_ignored(self):
        self.r = self._create_factory(os.path.join(os.path.dirname(__file__), 'something'))
        self._is_resolved(self.r)

    def test_resourcefactory_finds_imported_resource_when_similar_ignore_name(self):
        self.r = self._create_factory(os.path.dirname(__file__))
        imp = _Import(None, os.path.join(os.path.dirname(__file__)+'2', 'foo'))
        self._is_resolved(self.r, imp)

    def test_resourcefactory_ignores_imported_resource_when_relative_import(self):
        self.r = self._create_factory(os.path.abspath('.'))
        imp = _Import(None, os.path.join('.', 'foo'))
        self.assertEqual(None, self.r.get_resource_from_import(imp, self._context))

    def test_resourcefactory_finds_imported_resource_from_python_path(self):
        self.r = _ResourceFactory(FakeSettings())
        self.r.from_path = os.path.dirname(__file__)
        self._is_resolved(self.r)

    def test_resourcefactory_ignores_imported_resource_from_python_path(self):
        self.r = self._create_factory(os.path.dirname(__file__))
        self.r.from_path = os.path.dirname(__file__)
        self.assertEqual(None, self.r.get_resource_from_import(self._import, self._context))

    if IS_WINDOWS:

        def test_case_insensitive_ignore_upper(self):
            self._ignore_import(os.path.dirname(__file__).upper())

        def test_case_insensitive_ignore_lower(self):
            self._ignore_import(os.path.dirname(__file__).lower())

        def test_case_insensitive_ignore_relative_with_pattern(self):
            self._ignore_import(os.path.join('*', os.path.dirname(__file__)))

    def _ignore_import(self, exclude_directory):
        self.r = self._create_factory(exclude_directory)
        self.assertEqual(None, self.r.get_resource_from_import(self._import, self._context))

    def _create_factory(self, excluded_dir):
        settings = FakeSettings()
        settings.set('default directory', os.path.dirname(__file__))
        settings.excludes.update_excludes([excluded_dir])
        return _ResourceFactory(settings)

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
