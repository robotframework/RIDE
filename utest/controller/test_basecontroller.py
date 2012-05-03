import unittest
from robotide.controller.basecontroller import WithNamespace
from robotide.namespace.namespace import Namespace
from robotide.preferences.settings import Settings

class TestWithNamespace(unittest.TestCase):

    def test_get_all_cached_library_names(self):
        with_namespace = WithNamespace()
        with_namespace._set_namespace(namespace=self._create_namespace())
        print with_namespace.get_all_cached_library_names()

    def _create_namespace(self):
        settings = lambda:0
        settings.get = lambda k, d: d
        settings.add_change_listener = lambda *args:0
        namespace = Namespace(settings=settings)
        return namespace


if __name__ == '__main__':
    unittest.main()
