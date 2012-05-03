import unittest
from robotide.controller.filecontrollers import ResourceFileController
from robotide.namespace.suggesters import ResourceSuggester, LibrarySuggester
from robotide.spec.xmlreaders import LibrarySpec


class _ImportSuggesterTests(object):

    def setUp(self):
        self._suggester = self._create_suggester(['foofoo'], ['foofoo', 'foobar', 'barbar', 'doodoo'])

    def test_all_suggestions_with_empty_string(self):
        self.assertEqual(['barbar', 'doodoo', 'foobar'], self._suggestion_names(''))

    def test_only_matching_suggestion(self):
        self.assertEqual(['foobar'], self._suggestion_names('foo'))

    def test_multiple_matching_suggestions(self):
        self.assertEqual(['barbar', 'foobar'], self._suggestion_names('bar'))

    def test_no_matching_suggestions(self):
        self.assertEqual([], self._suggestion_names('zoo'))

    def _controller(self, imports=(), resources=(), libraries=()):
        controller = lambda:0
        controller.datafile_controller = controller
        controller.relative_path_to = lambda other: other.display_name
        controller.imports = [self._import(i) for i in imports]
        controller._chief_controller = controller
        controller.resources = [self._resource(r) for r in resources]
        controller.libraries = [self._library(l) for l in libraries]
        return controller

    def _resource(self, name):
        data = lambda:0
        data.source = name
        data.directory = '.'
        resource = ResourceFileController(data)
        return resource

    def _library(self, name):
        libSpec = lambda:0
        libSpec.name = name
        return libSpec

    def _import(self, name):
        imp = lambda:0
        imp.name = name
        return imp

    def _suggestion_names(self, value):
        return [s.name for s in self._suggester.get_suggestions(value)]


class TestResourceSuggester(_ImportSuggesterTests, unittest.TestCase):

    def _create_suggester(self, already_imported=(), available=()):
        return ResourceSuggester(self._controller(imports=already_imported, resources=available))


class TestLibrarySuggester(_ImportSuggesterTests, unittest.TestCase):

    def _create_suggester(self, already_imported=(), available=()):
        return LibrarySuggester(self._controller(imports=already_imported, libraries=available))


if __name__ == '__main__':
    unittest.main()
