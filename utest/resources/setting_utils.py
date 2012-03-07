import os
import stat
import unittest

from robotide.preferences.settings import Settings


class TestSettingsHelper(unittest.TestCase):

    def setUp(self, settings=None):
        self._init_settings_paths()
        if not settings:
            settings = Settings
        self.settings = settings(self.user_settings_path)

    def _init_settings_paths(self):
        self.settings_path = os.path.join(os.path.dirname(__file__),
                                          'settings.cfg')
        self.user_settings_path = os.path.join(os.path.dirname(__file__),
                                          'user.cfg')
        self.read_only_path = os.path.join(os.path.dirname(__file__), 'read-only.cfg')
        os.chmod(self.read_only_path, stat.S_IRUSR)


    def tearDown(self):
        for path in [self.settings_path, self.user_settings_path]:
            self._remove_path(path)

    def _remove_path(self, path):
        if os.path.exists(path):
                os.remove(path)

    def _check_content(self, expected_dict, check_self_settings=True):
        settings = Settings(self.user_settings_path)
        self.assertEquals(settings._config_obj, expected_dict)
        if check_self_settings:
            self.assertEquals(self.settings._config_obj, expected_dict)

    def _write_settings(self, content, path=None):
        f = open(self._get_path(path), 'w')
        f.write(content)
        f.close()

    def _read_settings_file_content(self, path=None):
        f = open(self._get_path(path), 'r')
        value = f.read()
        f.close()
        return value

    def _get_path(self, path):
        if path:
            return path
        return self.user_settings_path

    def _create_invalid_settings_file(self, path=None):
        self._write_settings('invalid = invalid', path)

    def _read_settings(self, path=None):
        try:
            return Settings(self._get_path(path))
        except:
            print self._read_settings_file_content()
            raise
