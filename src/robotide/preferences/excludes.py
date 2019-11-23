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
from fnmatch import fnmatch
import os
import wx

if wx.VERSION >= (3, 0, 3, ''):  # DEBUG wxPhoenix
    from wx.adv import HyperlinkCtrl, EVT_HYPERLINK
else:
    from wx import HyperlinkCtrl, EVT_HYPERLINK

from robotide.widgets import Dialog, HtmlWindow
from .widgets import PreferencesPanel


class Excludes():

    def __init__(self, directory):
        self._settings_directory = directory
        self._exclude_file_path = os.path.join(self._settings_directory, 'excludes')

    def get_excludes(self, separator='\n'):
        return separator.join(self._get_excludes())

    def _get_excludes(self):
        with self._get_exclude_file('r') as exclude_file:
            if not exclude_file:
                return set()
            return set(exclude_file.read().split())

    def remove_path(self, path):
        path = self._normalize(path)
        excludes = self._get_excludes()
        self.write_excludes(set([e for e in excludes if e != path]))

    def write_excludes(self, excludes):
        excludes = [self._normalize(e) for e in excludes]
        with self._get_exclude_file(read_write='w') as exclude_file:
            for exclude in excludes:
                if not exclude:
                    continue
                exclude_file.write("%s\n" % exclude)
        # print("DEBUG:real excluded self._get_excludes()=%s\n" % self._get_excludes())

    def update_excludes(self, new_excludes):
        excludes = self._get_excludes()
        self.write_excludes(excludes.union(new_excludes))
        # print("DEBUG: Excludes, excluded, union %s, %s, %s\n" % (excludes, new_excludes, excludes.union(new_excludes)))

    def _get_exclude_file(self, read_write):
        if not os.path.exists(self._exclude_file_path) and read_write.startswith('r'):
            if not os.path.isdir(self._settings_directory):
                os.makedirs(self._settings_directory)
            return open(self._exclude_file_path, 'w+')
        if os.path.isdir(self._exclude_file_path):
            raise NameError('"%s" is a directory, not file' % self._exclude_file_path)
        try:
            return open(self._exclude_file_path, read_write)
        except IOError as e:
            raise e #TODO FIXME

    def contains(self, path, excludes=None):
        if not path:
            return False
        excludes = excludes or self._get_excludes()
        if len(excludes) < 1:
            return False
        path = self._normalize(path)
        excludes = [self._normalize(e) for e in excludes]
        # print("DEBUG: excludes contains %s path %s\n"
        #      "any: %s\n" % (excludes[0], path, any(self._match(path, e) for e in excludes)) )
        return any(self._match(path, e) for e in excludes)

    def _match(self, path, e):
        return fnmatch(path, e) or path.startswith(e)

    def _normalize(self, path):
        if not (path or path.strip()):
            return None
        path = os.path.normcase(os.path.normpath(path))
        ext = os.path.splitext(path)[1]
        if not ext and not path.endswith(('*', '?', ']')):
            path += os.sep
            if '*' in path or '?' in path or ']' in path:
                path += '*'
        return path


class ExcludePreferences(PreferencesPanel):
    location = ('Excludes')
    title = 'Excludes'

    def __init__(self, settings, *args, **kwargs):
        super(ExcludePreferences, self).__init__(*args, **kwargs)
        self._settings = settings
        self._create_sizer()

    def _create_sizer(self):
        sizer = wx.BoxSizer(orient=wx.VERTICAL)
        self._add_help_dialog(sizer)
        self._add_text_box(sizer)
        self._add_button_and_status(sizer)
        self.SetSizer(sizer)

    def _add_help_dialog(self, sizer):
        # DEBUG wxPhoenix
        sizer.Add(HyperlinkCtrl(self, wx.ID_ANY, '', 'Need help?'))
        self.Bind(EVT_HYPERLINK, self.OnHelp)

    def _add_text_box(self, sizer):
        self._text_box = wx.TextCtrl(self,
            style=wx.TE_MULTILINE,
            size=wx.Size(570, 100),
            value=self._settings.excludes.get_excludes())
        sizer.Add(self._text_box, proportion=wx.EXPAND)

    def _add_button_and_status(self, sizer):
        # DEBUG wxPhoenix
        status_and_button_sizer = wx.GridSizer(rows=1, cols=2, vgap=10, hgap=10)
        status_and_button_sizer.Add(wx.Button(self, id=wx.ID_SAVE))
        self.Bind(wx.EVT_BUTTON, self.OnSave)
        self._status_label = wx.StaticText(self)
        status_and_button_sizer.Add(self._status_label)
        sizer.Add(status_and_button_sizer)

    def OnSave(self, event):
        text = self._text_box.GetValue()
        self._settings.excludes.write_excludes(set(text.split('\n')))
        save_label = 'Saved at %s. Reload the project for changes to take an effect.' % datetime.now().strftime('%H:%M:%S')
        self._status_label.SetLabel(save_label)

    def OnHelp(self, event):
        dialog = ExcludeHelpDialog()
        dialog.Show()


class ExcludeHelpDialog(Dialog):
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
                Pattern C:\MyProject\?oo matches:
                <ul>
                    <li>C:\MyProject\\foo</li>
                    <li>C:\MyProject\\boo</li>
                    <li><i>etc.</i></li>
                </ul>
            </td>
        </tr>
        <tr>
            <td valign="top" align="center">[seq]</td>
            <td valign="top" align="center">matches any character in <i>seq</i></td>
            <td valign="top" align="left">
               Pattern C:\MyProject\[bf]oo matches:
                <ul>
                    <li>C:\MyProject\\foo</li>
                    <li>C:\MyProject\\boo</li>
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
        Dialog.__init__(self, title='Help: excludes')
        # set Left to Right direction (while we don't have localization)
        self.SetLayoutDirection(wx.Layout_LeftToRight)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(HtmlWindow(self, (800, 600), self.help),
                  1,
                  flag=wx.EXPAND)
        self.SetSizerAndFit(sizer)

    def OnKey(self, *args):
        pass

    def close(self):
        self.Destroy()
