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

from datetime import datetime

import wx
from wx import Colour
from wx.adv import HyperlinkCtrl, EVT_HYPERLINK

from .preferences_dialogs import PreferencesPanel
from ..publish.messages import RideSettingsChanged
from ..widgets import RIDEDialog, HtmlWindow


class ExcludePreferences(PreferencesPanel):
    location = 'Excludes'
    title = 'Excludes'

    def __init__(self, settings, *args, **kwargs):
        super(ExcludePreferences, self).__init__(*args, **kwargs)
        self._settings = settings
        self._general_settings = self._settings['General']
        self.font = self.GetFont()
        self.font.SetFaceName(self._general_settings['font face'])
        self.font.SetPointSize(self._general_settings['font size'])
        self.SetFont(self.font)
        self.SetBackgroundColour(Colour(self._general_settings['background']))
        self.color_secondary_background = Colour(self._general_settings['secondary background'])
        self.SetForegroundColour(Colour(self._general_settings['foreground']))
        self.color_secondary_foreground = Colour(self._general_settings['secondary foreground'])
        self._create_sizer()

    def _create_sizer(self):
        sizer = wx.BoxSizer(orient=wx.VERTICAL)
        self._add_help_dialog(sizer)
        self._add_fs_exclusion_help(sizer)
        self._add_text_box(sizer)
        self._add_button_and_status(sizer)
        self.SetSizer(sizer)

    def _add_help_dialog(self, sizer):
        need_help = HyperlinkCtrl(self, wx.ID_ANY, '', 'Need help?')
        need_help.SetBackgroundColour(Colour(self.color_secondary_background))
        need_help.SetForegroundColour(Colour(self.color_secondary_foreground))
        sizer.Add(need_help)
        self.Bind(EVT_HYPERLINK, self.on_help)

    def _add_fs_exclusion_help(self, sizer):
        exclude_help = wx.StaticText(self, label='Since v2.0.8, files are also excluded from filesystem'
                                                 ' monitoring changes.')
        exclude_help.SetBackgroundColour(Colour(self._general_settings['background']))
        exclude_help.SetForegroundColour(Colour(self._general_settings['foreground']))
        sizer.Add(exclude_help)

    def _add_text_box(self, sizer):
        self._text_box = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_NOHIDESEL, size=wx.Size(570, 100),
                                     value=self._settings.excludes.get_excludes())
        self._text_box.SetBackgroundColour(Colour(self.color_secondary_background))
        self._text_box.SetForegroundColour(Colour(self.color_secondary_foreground))
        sizer.Add(self._text_box, proportion=wx.EXPAND)

    def _add_button_and_status(self, sizer):
        # DEBUG wxPhoenix
        status_and_button_sizer = wx.GridSizer(rows=1, cols=2, vgap=10, hgap=10)
        save_button = wx.Button(self, id=wx.ID_SAVE)
        save_button.SetBackgroundColour(Colour(self.color_secondary_background))
        save_button.SetForegroundColour(Colour(self.color_secondary_foreground))
        status_and_button_sizer.Add(save_button)
        self.Bind(wx.EVT_BUTTON, self.on_save)
        self._status_label = wx.StaticText(self)
        status_and_button_sizer.Add(self._status_label)
        sizer.Add(status_and_button_sizer)

    def on_save(self, event):
        __ = event
        text = self._text_box.GetValue()
        self._settings.excludes.write_excludes(set(text.split('\n')))
        RideSettingsChanged(keys=('Excludes', 'saved'), old=None, new=None).publish()
        save_label = 'Saved at %s. Reload the project for changes to take an effect.' %\
                     datetime.now().strftime('%H:%M:%S')
        self._status_label.SetLabel(save_label)

    @staticmethod
    def on_help(event):
        __ = event
        dialog = ExcludeHelpDialog()
        dialog.Show()


class ExcludeHelpDialog(RIDEDialog):
    def _execute(self):
        """ Just ignore it """
        pass

    help = """<font size="5">
<h1>Excludes</h1>
<p>
Paths to excludes are described in the text box, one exclude per row.
These excludes are saved in a file which is located at $HOME/.robotframework/ride/excludes on POSIX-systems and
%APPDATA%\\RobotFramework\\ride\\excludes on Windows.
</p>
<p>
You can edit excludes yourself using either the text box or editing the file with an editor. After hitting "Save", close
the Preferences window and reload the project to make the edited exludes to take effect. You can reload the project by
selecting "File" from the main menu bar and then selecting your project from the list in view.
</p>
<h2>Patterns in paths</h2>
<p>
RIDE supports defining excludes with absolute paths. You can achieve relative paths with path patterns which are
also supported.
</p>
<p>
The following shell-style wildcards are supported:
<table width="100%" border="1">
    <thead>
        <th><b>Pattern</b></th>
        <th><b>Meaning</b></th>
        <th><b>Examples</b></th>
    </thead>
    <tbody>
        <tr>
            <td valign="top" align="center">*</td>
            <td valign="top" align="center">matches everything</td>
            <td valign="top" align="left">
                Pattern /foo/*/quu matches:
                <ul>
                    <li>/foo/bar/quu</li>
                    <li>/foo/corge/quu</li>
                    <li><i>etc.</i></li>
                </ul>
            </td>
        </tr>
        <tr>
            <td valign="top" align="center">?</td>
            <td valign="top" align="center">matches any single character</td>
            <td valign="top" align="left">
                Pattern C:\\MyProject\\?oo matches:
                <ul>
                    <li>C:\\MyProject\\foo</li>
                    <li>C:\\MyProject\\boo</li>
                    <li><i>etc.</i></li>
                </ul>
            </td>
        </tr>
        <tr>
            <td valign="top" align="center">[seq]</td>
            <td valign="top" align="center">matches any character in <i>seq</i></td>
            <td valign="top" align="left">
               Pattern C:\\MyProject\\[bf]oo matches:
                <ul>
                    <li>C:\\MyProject\\foo</li>
                    <li>C:\\MyProject\\boo</li>
                    <li><i>and nothing else</i></li>
                </ul>
            </td>
        </tr>
        <tr>
            <td valign="top" align="center">[!seq]</td>
            <td valign="top" align="center">matches any character not in <i>seq</i></td>
            <td valign="top" align="left">
                Pattern /foo/[!q]uu matches:
                <ul>
                    <li>/foo/zuu</li>
                    <li><i>etc.</i></li>
                </ul>
                But does not match:
                <ul>
                    <li>/foo/quu</li>
                </ul>
            </td>
        </tr>
    </tbody>
</table>
</p>
</font>"""

    def __init__(self):
        RIDEDialog.__init__(self, title='Help: excludes')
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(HtmlWindow(self, (800, 600), self.help),
                  1,
                  flag=wx.EXPAND)
        self.SetSizerAndFit(sizer)

    def on_key(self, *args):
        """ Just ignore it """
        pass

    def close(self):
        self.Destroy()
