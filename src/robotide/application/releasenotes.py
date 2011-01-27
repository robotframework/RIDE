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
<h2>Release notes for 0.32</h2>
<table border="1">
<tr>
<td><b>ID</b></td>
<td><b>Type</b></td>
<td><b>Priority</b></td>
<td><b>Summary</b></td>
<td><b>AllLabels</b></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=57">Issue 57</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Possibility to execute test cases</td>
<td>Type-Enhancement, Priority-High, Target-0.32</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=647">Issue 647</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Find places where library keywords have been used</td>
<td>Type-Enhancement, Priority-High, Target-0.32</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=653">Issue 653</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Importing library with mutable object as argument fails</td>
<td>Type-Defect, Priority-Medium, Target-0.32</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=662">Issue 662</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Testcase Edit button on Setup/Teardown/Tags/Timeout/Template missing on OSX</td>
<td>Type-Defect, Priority-Medium, Target-0.32</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=670">Issue 670</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Escaped empty cells at the end of line are ignored and lost if file is saved</td>
<td>Type-Defect, Priority-Medium, Target-0.32</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=673">Issue 673</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Setup/teardown is not highlighted if those have arguments</td>
<td>Type-Defect, Priority-Medium, Target-0.32</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=674">Issue 674</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Undoing extract variable does not remove created variable from tree</td>
<td>Type-Defect, Priority-Medium, Target-0.32</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=676">Issue 676</a></td>
<td>Defect</td>
<td>Medium</td>
<td>New project is not added to recent files</td>
<td>Type-Defect, Priority-Medium, Target-0.32</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=677">Issue 677</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Drag and Drop flickers</td>
<td>Type-Defect, Target-0.32, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=681">Issue 681</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Delete doesn't work properly in Manage Run Configuration</td>
<td>Type-Defect, Priority-Medium, Target-0.32</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=615">Issue 615</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>It should be possible to add variables via tree context menu</td>
<td>Type-Enhancement, Priority-Medium, Target-0.32</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=652">Issue 652</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Unix-style line endings in windows</td>
<td>Type-Enhancement, Priority-Medium, Target-0.32</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=665">Issue 665</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Find Usages dialog should have way to go back to the keyword in question </td>
<td>Usability, Type-Enhancement, Target-0.32, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=672">Issue 672</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Renaming might take long time and jam the RIDE</td>
<td>Type-Enhancement, Target-0.32, Priority-Medium, Usability, Performance</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=679">Issue 679</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Allow disabling and enabling menu items, toolbar buttons and shortcuts from plugin API</td>
<td>Target-0.32, Type-Enhancement, Priority-Medium</td>
</tr>
</table>
<p>Altogether 15 issues.</p>
"""
