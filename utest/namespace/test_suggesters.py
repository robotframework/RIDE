import unittest
from robotide.controller.filecontrollers import ResourceFileController
from robotide.namespace.suggesters import ResourceSuggester

class TestResourceSuggester(unittest.TestCase):

    def test_getting_a_suggestion(self):
        suggester = ResourceSuggester(self._controller(imports=['foofoo.txt'], resources=['foofoo.txt', 'foobar.txt', 'barbar.txt']))
        self.assertEqual(['foobar.txt'], self._suggestion_names(suggester, 'foo'))
        self.assertEqual(['barbar.txt', 'foobar.txt'], self._suggestion_names(suggester, 'bar'))
        self.assertEqual([], self._suggestion_names(suggester, 'zoo'))

    def _suggestion_names(self, suggester, value):
        return [s.name for s in suggester.get_suggestions(value)]

    def _controller(self, imports=(), resources=()):
        controller = lambda:0
        controller.datafile_controller = controller
        controller.relative_path_to = lambda other: other.display_name
        controller.imports = [self._import(i) for i in imports]
        controller._chief_controller = controller
        controller.resources = [self._resu(r) for r in resources]
        return controller

    def _resu(self, name):
        data = lambda:0
        data.source = name
        data.directory = '.'
        resource = ResourceFileController(data)
        return resource

    def _import(self, name):
        imp = lambda:0
        imp.name = name
        return imp


if __name__ == '__main__':
    unittest.main()
