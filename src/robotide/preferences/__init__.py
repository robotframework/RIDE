#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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

from .settings import Settings, initialize_settings, RideSettings
from .editor import PreferenceEditor
from .widgets import PreferencesPanel, PreferencesComboBox,\
    PreferencesColorPicker
from .imports import ImportPreferences
from .saving import SavingPreferences
from .editors import GridEditorPreferences, TextEditorPreferences,\
    TestRunnerPreferences
from .excludes import ExcludePreferences


class Preferences(object):

    def __init__(self, settings):
        self.settings = settings
        self._preference_panels = []
        self._add_builtin_preferences()

    @property
    def preference_panels(self):
        return self._preference_panels

    def add(self, prefrence_ui):
        if prefrence_ui not in self._preference_panels:
            self._preference_panels.append(prefrence_ui)

    def remove(self, panel_class):
        if panel_class in self._preference_panels:
            self._preference_panels.remove(panel_class)

    def _add_builtin_preferences(self):
        self.add(SavingPreferences)
        self.add(ImportPreferences)
        self.add(GridEditorPreferences)
        self.add(TextEditorPreferences)
        self.add(TestRunnerPreferences)
        self.add(ExcludePreferences)
