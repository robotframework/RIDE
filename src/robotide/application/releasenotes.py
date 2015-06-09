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
<h2>Release notes for 1.4b3</h2>
<table border="1">
<tr>
<td><p><b>ID</b></p></td>
<td><p><b>Type</b></p></td>
<td><p><b>Priority</b></p></td>
<td><p><b>Summary</b></p></td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1446">Issue 1446</a></td>
<td>enhancement</td>
<td>critical</td>
<td>Robot Framework 2.8 compatibility</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1371">Issue 1371</a></td>
<td>bug</td>
<td>high</td>
<td>Use installed RF to list standard libraries</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1449">Issue 1449</a></td>
<td>enhancement</td>
<td>medium</td>
<td>Grid editor columns auto-resize</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1395">Issue 1395</a></td>
<td>bug</td>
<td>medium</td>
<td>RIDE IndexError during test execution</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1370">Issue 1370</a></td>
<td>bug</td>
<td>medium</td>
<td>'View All Tags (F7)' does not work if there are multiple identical tags with different case(upper/lower)</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1249">Issue 1249</a></td>
<td>bug</td>
<td>medium</td>
<td>Text box stuck on UI when renaming a test suite</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1248">Issue 1248</a></td>
<td>bug</td>
<td>medium</td>
<td>Lib directory included twice into the source distribution</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1162">Issue 1162</a></td>
<td>enhancement</td>
<td>medium</td>
<td>Preferences dialog has no action button to refresh the display</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1105">Issue 1105</a></td>
<td>enhancement</td>
<td>medium</td>
<td>Run Keyword If argument enhancement</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1455">Issue 1455</a></td>
<td>bug</td>
<td>low</td>
<td>Grid colorizer does not recognize changed settings.</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1443">Issue 1443</a></td>
<td>bug</td>
<td>low</td>
<td>Import library spec dialog does not work on OSX</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1403">Issue 1403</a></td>
<td>bug</td>
<td>low</td>
<td>RIDE doesn't restore to the un-minimised size, if it is closed when minimised.</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1402">Issue 1402</a></td>
<td>bug</td>
<td>low</td>
<td>"New version of RIDE available"-dialog has wrong download URL </td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1401">Issue 1401</a></td>
<td>enhancement</td>
<td>low</td>
<td>Option to use monospace font in grid</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1317">Issue 1317</a></td>
<td>enhancement</td>
<td>low</td>
<td>Bad error message when Robot Framework is not installed</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1277">Issue 1277</a></td>
<td>bug</td>
<td>low</td>
<td>New resource file name is lower cased in Windows</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/837">Issue 837</a></td>
<td>bug</td>
<td>low</td>
<td>Tag display only half visible</td>
</tr>
</table>
<p>Altogether 17 issues.</p>
"""
