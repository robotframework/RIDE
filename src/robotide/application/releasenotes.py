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
<h2>Release notes for 0.36</h2>
<table border="1">
<tr>
<td><b>ID</b></td>
<td><b>Type</b></td>
<td><b>Priority</b></td>
<td><b>Summary</b></td>
<td><b>AllLabels</b></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=831">Issue 831</a></td>
<td>Enhancement</td>
<td>Critical</td>
<td>Support for RF 2.6 Keyword Teardown</td>
<td>Priority-Critical, Target-0.36, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=792">Issue 792</a></td>
<td>Defect</td>
<td>High</td>
<td>Renaming from grid fails when differing case</td>
<td>Priority-High, Target-0.36, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=729">Issue 729</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Bundle Robot Framework with RIDE to ease handling dependencies</td>
<td>Priority-High, Type-Enhancement, Usability, target-0.36</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=789">Issue 789</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Variable rename when new normalized name is the same as the original fails</td>
<td>Priority-Medium, Target-0.36, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=790">Issue 790</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Add keyword from tree when suite is collapsed produces traceback</td>
<td>Priority-Medium, Target-0.36, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=791">Issue 791</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Cell values, keyword names, and test names with two spaces break in txt format</td>
<td>Priority-Medium, Target-0.36, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=797">Issue 797</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Undoing while editing grid undoes operations before edit</td>
<td>Priority-Medium, Target-0.36, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=813">Issue 813</a></td>
<td>Defect</td>
<td>Medium</td>
<td>RIDE run tab doesn't respect the --outputdir option.</td>
<td>Priority-Medium, Target-0.36, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=815">Issue 815</a></td>
<td>Defect</td>
<td>Medium</td>
<td>resources listed twice due to case sensitive path</td>
<td>Priority-Medium, Target-0.36, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=817">Issue 817</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Test case copied with RIDE loses default tags</td>
<td>Priority-Medium, Target-0.36, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=818">Issue 818</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Problem while renaming(Adding or deleting underscore in test case name)</td>
<td>Priority-Medium, Target-0.36, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=826">Issue 826</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Test runner plugin doesn't handler non-ASCII characters in test case names</td>
<td>Priority-Medium, Target-0.36, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=478">Issue 478</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>RIDE should allow inserting rows instead of overwriting existing ones when doing the paste action.</td>
<td>Priority-Medium, Target-0.36, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=796">Issue 796</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Create keyword should ignore BDD prefixes</td>
<td>Priority-Medium, Target-0.36, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=834">Issue 834</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>A human readable error message when wx is not installed</td>
<td>Priority-Medium, Target-0.36, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=785">Issue 785</a></td>
<td>Enhancement</td>
<td>Low</td>
<td>Show the filename in window title</td>
<td>Priority-Low, Target-0.36, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=835">Issue 835</a></td>
<td>Enhancement</td>
<td>Low</td>
<td>Leaving setting editor empty should remove the setting instead of complaining about empty value</td>
<td>Priority-Low, Target-0.36, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=836">Issue 836</a></td>
<td>Enhancement</td>
<td>Low</td>
<td>Selecting item from tree should change to edit tab unless is has some effect in the current tab</td>
<td>Priority-Low, Target-0.36, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=838">Issue 838</a></td>
<td>Enhancement</td>
<td>Low</td>
<td>Keyboard shortcuts for New Test Case, Keyword, Copy, Insert/Delete Row, Add Scalar and List Variable</td>
<td>Priority-Low, Target-0.36, Type-Enhancement</td>
</tr>
</table>
<p>Altogether 19 issues.</p>
"""
