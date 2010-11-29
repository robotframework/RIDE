#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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
<h2>Release notes for 0.30</h2>
<table border="1">
<tr>
<td><b>ID</b></td>
<td><b>Type</b></td>
<td><b>Priority</b></td>
<td><b>Summary</b></td>
<td><b>AllLabels</b></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=268">Issue 268</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Possibility to move variables between suites and resource files</td>
<td>Type-Enhancement, Target-0.30, Priority-High</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=596">Issue 596</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Create link from imported resource to related item in the tree view</td>
<td>Type-Enhancement, Target-0.30, Priority-High</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=572">Issue 572</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Invalid plugin can cause RIDE to crash hard</td>
<td>Type-Defect, Priority-Medium, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=590">Issue 590</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Test suite file is not reloaded when changed outside the editor</td>
<td>Type-Defect, Priority-Medium, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=591">Issue 591</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Touching a test suite file crashes the editor</td>
<td>Target-0.30, Type-Defect, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=594">Issue 594</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Content assist should choose between left/right of the cell and below/above based on where there is more space</td>
<td>Type-Defect, Priority-Medium, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=600">Issue 600</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Commenting doesn't work with 0.29.*</td>
<td>Type-Defect, Priority-Medium, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=601">Issue 601</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Insert Rows does not work correctly with FOR loops</td>
<td>Type-Defect, Priority-Medium, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=602">Issue 602</a></td>
<td>Defect</td>
<td>Medium</td>
<td>RIDE gets stucked in "File Changed On Disk" -dialog</td>
<td>Type-Defect, Priority-Medium, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=607">Issue 607</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Cannot modify contents inside a FOR loop in RIDE.</td>
<td>Type-Defect, Priority-Medium, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=609">Issue 609</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Keyword search shows resource keywords twice</td>
<td>Type-Defect, Priority-Medium, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=532">Issue 532</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>It should be possible to move lines up/down in grid</td>
<td>Type-Enhancement, Priority-Medium, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=552">Issue 552</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Allow selecting tree node based on controller through plugin API</td>
<td>Type-Enhancement, Priority-Medium, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=569">Issue 569</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Support saving using old metadata format</td>
<td>Type-Enhancement, Target-0.30, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=586">Issue 586</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>CTRL+Space in cell (without editing) should open suggestions</td>
<td>Type-Enhancement, Priority-Medium, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=598">Issue 598</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Resource file name in tree should be file name without formatting</td>
<td>Type-Enhancement, Priority-Medium, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=603">Issue 603</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>OpenSuite, OpenResource ans TestCaseAdded messages need the data items in their payload</td>
<td>Type-Enhancement, Priority-Medium, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=606">Issue 606</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>plugin manager should sort list of plugins</td>
<td>Type-Enhancement, Priority-Medium, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=565">Issue 565</a></td>
<td>Defect</td>
<td>Low</td>
<td>Keyword colorizer does not recognize renamed keyword immediately</td>
<td>Type-Defect, Priority-Low, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=604">Issue 604</a></td>
<td>Enhancement</td>
<td>Low</td>
<td>Log system information on startup</td>
<td>Type-Enhancement, Priority-Low, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=605">Issue 605</a></td>
<td>Enhancement</td>
<td>Low</td>
<td>Log should include traceback if an exception occured</td>
<td>Type-Enhancement, Priority-Low, Target-0.30</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=608">Issue 608</a></td>
<td>Enhancement</td>
<td>Low</td>
<td>Make txt default format for new files</td>
<td>Type-Enhancement, Priority-Low, Target-0.30</td>
</tr>
</table>
<p>Altogether 22 issues.</p>
"""
