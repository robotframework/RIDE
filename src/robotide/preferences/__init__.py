from .preferences_dialog import PreferencesDialog
from .preferences_panel import (PreferencesPanel, PreferencesComboBox,
    PreferencesColorPicker)
from .saving import SavingPreferences
from .colors import ColorPreferences


class Preferences(object):

    def __init__(self):
        self._preference_panels = []
        self._add_builtin_preferences()

    @property
    def preference_panels(self):
        return self._preference_panels

    def add(self, prefrence_ui):
        if prefrence_ui not in self._preference_panels:
            self._preference_panels.append(prefrence_ui)

    def remove(self):
        if panel_class in self._preference_panels:
            self._preference_panels.remove(panel_class)

    def _add_builtin_preferences(self):
        self.add(SavingPreferences)
        self.add(ColorPreferences)
