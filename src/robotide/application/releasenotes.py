#  Copyright 2008-2015 Nokia Solutions and Networks
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
from wx.lib.ClickableHtmlWindow import PyClickableHtmlWindow

from robotide.version import VERSION
from robotide.pluginapi import ActionInfo


class ReleaseNotes(object):
    """Shows release notes of the current version.

    The release notes tab will automatically be shown once per release.
    The user can also view them on demand by selecting "Release Notes"
    from the help menu.
    """

    def __init__(self, application):
        self.application = application
        settings =  application.settings
        self.version_shown = settings.get('version_shown', '')
        self._view = None
        self.enable()

    def enable(self):
        self.application.frame.actions.register_action(ActionInfo('Help', 'Release Notes', self.show,
                                        doc='Show the release notes'))
        self.show_if_updated()

    def show_if_updated(self):
        if self.version_shown != VERSION:
            self.show()
            self.application.settings['version_shown'] = VERSION

    def show(self, event=None):
        if not self._view:
            self._view = self._create_view()
            self.application.frame.notebook.AddPage(self._view, "Release Notes", select=False)
        self.application.frame.notebook.show_tab(self._view)

    def bring_to_front(self):
        if self._view:
            self.application.frame.notebook.show_tab(self._view)

    def _create_view(self):
        panel = wx.Panel(self.application.frame.notebook)
        html_win = PyClickableHtmlWindow(panel, -1)
        html_win.SetStandardFonts()
        html_win.SetPage(WELCOME_TEXT + RELEASE_NOTES)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(html_win, 1, wx.EXPAND|wx.ALL, border=8)
        panel.SetSizer(sizer)
        return panel


WELCOME_TEXT = """
<h2>Welcome to use RIDE version %s</h2>

<p>Thank you for using the Robot Framework IDE (RIDE).</p>

<p>Visit RIDE on the web:</p>

<ul>
  <li><a href="https://github.com/robotframework/RIDE">
      RIDE project page on github</a></li>
  <li><a href="https://github.com/robotframework/RIDE/wiki/Installation-Instructions">
      Installation instructions</a></li>
  <li><a href="https://github.com/robotframework/RIDE/wiki/Release-notes">
      Release notes</a></li>
</ul>
""" % VERSION

# *** DO NOT EDIT THE CODE BELOW MANUALLY ***
# Release notes are updated automatically by package.py script whenever
# a numbered distribution is created.
RELEASE_NOTES = """
<h2>Release notes for 1.5.1</h2>
<table border="1">
<tr>
<td><p><b>ID</b></p></td>
<td><p><b>Type</b></p></td>
<td><p><b>Priority</b></p></td>
<td><p><b>Summary</b></p></td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/http://github.com/robotframework/RIDE/issues/">Issue http://github.com/robotframework/RIDE/issues/</a></td>
<td>bug</td>
<td>high</td>
<td>Error in RIDE startup</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/http://github.com/robotframework/RIDE/issues/">Issue http://github.com/robotframework/RIDE/issues/</a></td>
<td>bug</td>
<td>high</td>
<td>Problem with opening two ride </td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/http://github.com/robotframework/RIDE/issues/">Issue http://github.com/robotframework/RIDE/issues/</a></td>
<td>bug</td>
<td>high</td>
<td>Should not crash when removing old log files fails</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/http://github.com/robotframework/RIDE/issues/">Issue http://github.com/robotframework/RIDE/issues/</a></td>
<td>bug</td>
<td>medium</td>
<td>It is possible to create suite variables with a blank space before the $, @ or &</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/http://github.com/robotframework/RIDE/issues/">Issue http://github.com/robotframework/RIDE/issues/</a></td>
<td>bug</td>
<td>medium</td>
<td>Create Dictionary Variable is missing from the tree context menu</td>
</tr>
</table>
<p>Altogether 5 issues.</p>
"""
