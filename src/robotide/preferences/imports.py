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

import wx

from robotide.preferences import widgets


class ImportPreferences(widgets.PreferencesPanel):
    location = ('Importing')
    title = 'Library imports and PYTHONPATH'

    def __init__(self, parent, settings):
        super(widgets.PreferencesPanel, self).__init__(parent)
        self.SetSizer(wx.FlexGridSizer(rows=4, cols=2, vgap=10, hgap=5))
        self.Sizer.AddGrowableCol(1, proportion=1)
        self._add_settings(settings)

    def _add_settings(self, settings):
        list_settings = [
            ('auto imports', 'Comma separated list of libraries to be '
                             'automatically imported.'),
            ('pythonpath', 'Comma separated list of directories to be added '
                           'to PYTHONPATH when libraries are searched.'),
            ('library xml directories', 'Comma separated list of directories '
                                        'containing library spec files.')
        ]
        for (name, help) in list_settings:
            self._create_list_setting_editor(settings, name, help)

    def _create_list_setting_editor(self, settings, name, help):
        label, editor = widgets.comma_separated_value_editor(
            self, settings, name, name.capitalize(), help)
        self.Sizer.Add(label)
        self.Sizer.Add(editor, flag=wx.EXPAND)
