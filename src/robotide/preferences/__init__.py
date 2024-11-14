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

from .configobj.src.configobj import ConfigObj, ConfigObjError, Section, UnreprError
from .editor import PreferenceEditor
from .editors import GridEditorPreferences, TextEditorPreferences, TestRunnerPreferences
from .general import DefaultPreferences
from .imports import ImportPreferences
from .saving import SavingPreferences
from .settings import Settings, initialize_settings, RideSettings

import wx


class Languages:
    names = [('Bulgarian', 'bg-BG', wx.LANGUAGE_BULGARIAN), ('Bosnian', 'bs-BA', wx.LANGUAGE_BOSNIAN),
             ('Czech', 'cs-CZ', wx.LANGUAGE_CZECH), ('German', 'de-DE', wx.LANGUAGE_GERMAN),
             ('English', 'en-GB', wx.LANGUAGE_ENGLISH), ('Spanish', 'es-ES', wx.LANGUAGE_SPANISH),
             ('Finnish', 'fi-FI', wx.LANGUAGE_FINNISH), ('French', 'fr-FR', wx.LANGUAGE_FRENCH),
             ('Hindi', 'hi-IN', wx.LANGUAGE_HINDI), ('Italian', 'it-IT', wx.LANGUAGE_ITALIAN),
             ('Japanese', 'ja', wx.LANGUAGE_JAPANESE), # Since RF 7.0.1
             ('Korean', 'ko-KR', wx.LANGUAGE_KOREAN_KOREA),  # Future RF after 7.0.1
             ('Dutch', 'nl-NL', wx.LANGUAGE_DUTCH), ('Polish', 'pl-PL', wx.LANGUAGE_POLISH),
             ('Portuguese', 'pt-PT', wx.LANGUAGE_PORTUGUESE),
             ('Brazilian Portuguese', 'pt-BR', wx.LANGUAGE_PORTUGUESE_BRAZILIAN),
             ('Romanian', 'ro-RO', wx.LANGUAGE_ROMANIAN), ('Russian', 'ru-RU', wx.LANGUAGE_RUSSIAN),
             ('Swedish', 'sv-SE', wx.LANGUAGE_SWEDISH), ('Thai', 'th-TH', wx.LANGUAGE_THAI),
             ('Turkish', 'tr-TR', wx.LANGUAGE_TURKISH), ('Ukrainian', 'uk-UA', wx.LANGUAGE_UKRAINIAN),
             ('Vietnamese', 'vi-VN', wx.LANGUAGE_VIETNAMESE),
             ('Chinese Simplified', 'zh-CN', wx.LANGUAGE_CHINESE_SIMPLIFIED),
             ('Chinese Traditional', 'zh-TW', wx.LANGUAGE_CHINESE_TRADITIONAL)]


class Preferences(object):

    def __init__(self, settings):
        self.settings = settings
        self._preference_panels = []
        self._add_builtin_preferences()

    @property
    def preference_panels(self):
        return self._preference_panels

    def add(self, preference_ui):
        if preference_ui not in self._preference_panels:
            self._preference_panels.append(preference_ui)

    def remove(self, panel_class):
        if panel_class in self._preference_panels:
            self._preference_panels.remove(panel_class)

    def _add_builtin_preferences(self):
        from ..ui import ExcludePreferences
        self.add(DefaultPreferences)
        self.add(SavingPreferences)
        self.add(ImportPreferences)
        self.add(GridEditorPreferences)
        self.add(TextEditorPreferences)
        self.add(TestRunnerPreferences)
        self.add(ExcludePreferences)
