#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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
from robotide.pluginapi import Plugin, ActionInfo


class ReleaseNotesPlugin(Plugin):
    """Shows release notes of the current version.

    The release notes tab will automatically be shown once per release.
    The user can also view them on demand by selecting "Release Notes"
    from the help menu.
    """

    def __init__(self, application):
        Plugin.__init__(self, application, default_settings={'version_shown':''})
        self._view = None

    def enable(self):
        self.register_action(ActionInfo('Help', 'Release Notes', self.show,
                                        doc='Show the release notes'))
        self.show_if_updated()

    def disable(self):
        self.unregister_actions()
        self.delete_tab(self._view)
        self._view = None

    def show_if_updated(self):
        if self.version_shown != VERSION:
            self.show()
            self.save_setting('version_shown', VERSION)

    def show(self, event=None):
        if not self._view:
            self._view = self._create_view()
            self.notebook.AddPage(self._view, "Release Notes", select=False)
        self.show_tab(self._view)

    def bring_to_front(self):
        if self._view:
            self.show_tab(self._view)

    def _create_view(self):
        panel = wx.Panel(self.notebook)
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
  <li><a href="http://code.google.com/p/robotframework-ride/">
      RIDE project page on Google Code</a></li>
  <li><a href="http://code.google.com/p/robotframework-ride/wiki/InstallationInstructions">
      Installation instructions</a></li>
  <li><a href="http://code.google.com/p/robotframework-ride/wiki/ReleaseNotes">
      Release notes</a></li>
</ul>
""" % VERSION

# *** DO NOT EDIT THE CODE BELOW MANUALLY ***
# Release notes are updated automatically by package.py script whenever
# a numbered distribution is created.
RELEASE_NOTES = """
<h2>Release notes for 0.40</h2>
<table border="1">
<tr>
<td><b>ID</b></td>
<td><b>Type</b></td>
<td><b>Priority</b></td>
<td><b>Summary</b></td>
<td><b>AllLabels</b></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=899">Issue 899</a></td>
<td>Defect</td>
<td>High</td>
<td>Renaming a dirty Test Suite, gets its file deleted</td>
<td>Priority-High, Target-0.40, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=903">Issue 903</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Improved data formatting when saving</td>
<td>Priority-High, Target-0.40, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=904">Issue 904</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Support for editing test data in plain text format</td>
<td>Priority-High, Target-0.40, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=735">Issue 735</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Using # character to comment rows collapses the commented row on next startup</td>
<td>Priority-Medium, Target-0.40, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=876">Issue 876</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Bug in testrunner plugin, module SocketListener.py</td>
<td>Priority-Medium, Target-0.40, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=892">Issue 892</a></td>
<td>Defect</td>
<td>Medium</td>
<td>RIDE cannot create a new top level suite file</td>
<td>Priority-Medium, Target-0.40, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=893">Issue 893</a></td>
<td>Defect</td>
<td>Medium</td>
<td>RIDE - Problems in multiuser environment due to hard-coded port no.</td>
<td>Priority-Medium, Target-0.40, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=897">Issue 897</a></td>
<td>Defect</td>
<td>Medium</td>
<td>HTML files are always written using unix line separators</td>
<td>Priority-Medium, Target-0.40, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=901">Issue 901</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Show table headers in grid editor</td>
<td>Priority-Medium, Target-0.40, Type-Enhancement</td>
</tr>
</table>
<p>Altogether 9 issues.</p>
"""
