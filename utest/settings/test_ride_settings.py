import unittest
import os

from robotide.preferences import RideSettings


class TestRideSettings(unittest.TestCase):

    def test_loading_settings(self):
        settings = RideSettings()
        self.assertTrue(settings._config_obj["mainframe size"])


class TestGettingPath(unittest.TestCase):

    def test_get_path_without_parts(self):
        settings = RideSettings()
        self.assertTrue(settings.get_path().endswith('ride'))

    def test_get_path_with_one_part(self):
        settings = RideSettings()
        self.assertTrue(
            settings.get_path('foo').endswith('ride%sfoo' % os.sep))

    def test_get_path_with_three_parts(self):
        path = RideSettings().get_path('foo', 'bar', 'hello')
        expected_end = 'ride/foo/bar/hello'.replace('/', os.sep)
        self.assertTrue(path.endswith(expected_end))


if __name__ == "__main__":
    unittest.main()
