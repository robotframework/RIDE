#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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
<h2>Release notes for 0.39</h2>
<table border="1">
<tr>
<td><b>ID</b></td>
<td><b>Type</b></td>
<td><b>Priority</b></td>
<td><b>Summary</b></td>
<td><b>AllLabels</b></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=146">Issue 146</a></td>
<td>Defect</td>
<td>High</td>
<td>Keyword completion and documentation popups don't work on OSX</td>
<td>OS-OSX, Priority-High, Target-0.39, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=856">Issue 856</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Setting PYTHONPATH in RIDE</td>
<td>Priority-High, Target-0.39, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=165">Issue 165</a></td>
<td>Defect</td>
<td>Medium</td>
<td>The confirm exit -dialog is not closed when RIDE exists on OSX</td>
<td>OS-OSX, Priority-Medium, Target-0.39, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=444">Issue 444</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Manage Run Configuration screen can not be closed or dismissed on OSX</td>
<td>OS-OSX, Priority-Medium, Target-0.39, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=503">Issue 503</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Events are launched several times on new Macs</td>
<td>OS-OSX, Priority-Medium, Target-0.39, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=858">Issue 858</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Documentation popup appears when pointer is outside RIDE window</td>
<td>Priority-Medium, Target-0.39, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=265">Issue 265</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Changing resource file format should also update resource imports</td>
<td>Priority-Medium, Target-0.39, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=298">Issue 298</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Possibility to rename test case files</td>
<td>Priority-Medium, Target-0.39, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=299">Issue 299</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Possibility to delete test case files</td>
<td>Priority-Medium, Target-0.39, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=618">Issue 618</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>I want to search where my Resources are used</td>
<td>Priority-Medium, Target-0.39, Type-Enhancement, Usability</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=644">Issue 644</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Possibility to rename resource files</td>
<td>Priority-Medium, Target-0.39, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=855">Issue 855</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Cases In Run tab should not be expanded as default</td>
<td>Priority-Medium, Target-0.39, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=863">Issue 863</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Possibility to delete resource files </td>
<td>Priority-Medium, Target-0.39, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=502">Issue 502</a></td>
<td>Documentation</td>
<td>Medium</td>
<td>Document that on 64bit OSX, RIDE will not start unless 32bit Python is used</td>
<td>Priority-Medium, Target-0.39, Type-Documentation</td>
</tr>
</table>
<p>Altogether 14 issues.</p>
"""
