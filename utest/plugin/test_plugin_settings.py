import tempfile
import unittest
import os

from robotide.preferences.settings import Settings
from robotide.pluginapi import Plugin

from resources import TestSettingsHelper, FakeApplication


class TestPluginSettings(TestSettingsHelper):
    _settings_path = os.path.join(tempfile.gettempdir(), 'set.cfg')

    def tearDown(self):
        if os.path.exists(self._settings_path):
            os.remove(self._settings_path)

    def test_setting_default_settings_when_no_settings_exist(self):
        self.assertEquals(self._create_plugin().foo, 'bar')

    def test_set_default_settings_when_settings_exist(self):
        app = self._create_app()
        app.settings['Plugins'].add_section('MyPlug', foo='zip')
        self.assertEquals(Plugin(app, name='MyPlug').foo, 'zip')

    def test_save_setting_with_override(self):
        p = self._create_plugin()
        p.save_setting('foo', 'new')
        self.assertEquals(p.foo, 'new')

    def test_save_setting_without_override(self):
        p = self._create_plugin()
        p.save_setting('foo', 'new', override=False)
        self.assertEquals(p.foo, 'bar')

    def test_direct_attribute_access_with_existing_setting(self):
        self.assertEquals(self._create_plugin().foo, 'bar')

    def test_direct_attribute_access_with_non_existing_setting(self):
        try:
            self._create_plugin().non_existing
        except AttributeError:
            return
        raise AssertionError(
            "Accessing non existent attribute should raise AttributeError")

    def _create_plugin(self, settings={'foo': 'bar'}):
        return Plugin(
            self._create_app(), name='MyPlug', default_settings=settings)

    def _create_app(self):
        app = FakeApplication()
        settings = Settings(self._settings_path)
        settings.add_section('Plugins')
        app.settings = settings
        return app


if __name__ == "__main__":
    unittest.main()
