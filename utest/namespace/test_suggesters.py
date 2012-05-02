import unittest
from robotide.controller.filecontrollers import ResourceFileController
from robotide.namespace.suggesters import ResourceSuggester

class TestResourceSuggester(unittest.TestCase):

    def test_getting_a_suggestion(self):
        controller = lambda:0
        controller.datafile_controller = controller
        controller.relative_path_to = lambda other: other.display_name
        controller.imports = [self._import('foofoo.txt')]
        controller._chief_controller = controller
        controller.resources = [self._resu('foofoo.txt'), self._resu('foobar.txt')]
        suggester = ResourceSuggester(controller)
        self.assertEqual(['foobar.txt'], [s.name for s in suggester.get_suggestions('foo')])
        self.assertEqual(0, len(suggester.get_suggestions('zoo')))


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
