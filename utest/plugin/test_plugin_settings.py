#  Copyright 2008 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import unittest

from robotide.plugin import plugin

from resources import TestSettingsHelper, FakeApplication


class TestPluginSettings(TestSettingsHelper):
    
    def setUp(self):
        TestSettingsHelper.setUp(self)
        self.orig_plugin_settings = plugin.SETTINGS
        self.settings.add_section('Plugins')
        plugin.SETTINGS = self.settings

    def tearDown(self):
        TestSettingsHelper.tearDown(self)
        plugin.SETTINGS = self.orig_plugin_settings

    def testSettingDefaultSettingsWhenNoSettingsExist(self):
        self.assertEquals(self.App().foo, 'bar')

    def testSetDefaultSettingsWhenSettingsExist(self):
        self.settings['Plugins'].add_section('MyPlug')['foo'] = 'zip'
        self.assertEquals(self.App().foo, 'zip')

    def testSaveSettingWithOverride(self):
        p = self.App()
        p.save_setting('foo', 'new')
        self.assertEquals(p.foo, 'new')

    def testSaveSettingWithoutOverride(self):
        p = self.App()
        p.save_setting('foo', 'new', override=False)
        self.assertEquals(p.foo, 'bar')

    def testDirectAttributeAccessWithExistingSetting(self):
        self.assertEquals(self.App().foo, 'bar')

    def testDirectAttributeAccessWithNonExistingSetting(self):
        try:
            self.App().non_existing
        except AttributeError:
            return
        raise AssertionError("Accessing non existent attribute should raise AttributeError")

    def App(self, settings={'foo': 'bar'}):
        return plugin.Plugin(FakeApplication(), name='MyPlug', 
                             default_settings=settings)


if __name__ == "__main__":
    unittest.main()
