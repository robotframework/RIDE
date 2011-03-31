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
<h2>Release notes for 0.34</h2>
<table border="1">
<tr>
<td><b>ID</b></td>
<td><b>Type</b></td>
<td><b>Priority</b></td>
<td><b>Summary</b></td>
<td><b>AllLabels</b></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=733">Issue 733</a></td>
<td>Defect</td>
<td>High</td>
<td>Find Usages highlighting failure</td>
<td>Type-Defect, Priority-High, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=734">Issue 734</a></td>
<td>Defect</td>
<td>High</td>
<td>Row controls do not work from grid editor</td>
<td>Type-Defect, Priority-High, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=746">Issue 746</a></td>
<td>Defect</td>
<td>High</td>
<td>Settings button messes with the GUI layout and display</td>
<td>Type-Defect, Priority-High, Target-0.34, OS-Windows</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=753">Issue 753</a></td>
<td>Defect</td>
<td>High</td>
<td>Does not find library defined as relative path</td>
<td>Type-Defect, Priority-High, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=725">Issue 725</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Possibility to add arguments to Test Runner plugin</td>
<td>Type-Enhancement, Priority-High, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=728">Issue 728</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Remember whether settings are open or hidden</td>
<td>Type-Enhancement, Priority-High, Target-0.34, Usability</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=768">Issue 768</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Report/log links from run plugin do not work when generating them is disabled during execution and rebot is used to generate them</td>
<td>Type-Enhancement, Priority-High, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=199">Issue 199</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Delete button does not work in table cells</td>
<td>Type-Defect, Priority-Medium, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=655">Issue 655</a></td>
<td>Defect</td>
<td>Medium</td>
<td>moving rows up and down beyond screen scroll limit does not work</td>
<td>Type-Defect, Priority-Medium, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=730">Issue 730</a></td>
<td>Defect</td>
<td>Medium</td>
<td>New tag editing feature doesn't work well on MacOSX</td>
<td>Type-Defect, Priority-Medium, OS-OSX, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=732">Issue 732</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Ride 0.33 variable move-up move-down will lose focus</td>
<td>Type-Defect, Priority-Medium, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=740">Issue 740</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Popup shown over setup/teardown setting is not always closed</td>
<td>Type-Defect, Priority-Medium, Target-0.34, OS-Windows</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=741">Issue 741</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Focus follows mouse pointer in settings</td>
<td>Type-Defect, Priority-Medium, Target-0.34, Usability</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=745">Issue 745</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Test Runner plugin settings are shared between execution profiles</td>
<td>Type-Defect, Priority-Medium, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=752">Issue 752</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Copying from detached popup is not always possible</td>
<td>Type-Defect, Priority-Medium, Target-0.34, OS-Windows, Usability</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=756">Issue 756</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Tree hangs after keyword renaming</td>
<td>Type-Defect, Priority-Medium, Target-0.34, OS-Windows</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=760">Issue 760</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Copy Keyword dialog incorrectly shows that arguments can be changed</td>
<td>Priority-Medium, Target-0.34, Type-Defect</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=762">Issue 762</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Visible row and cell selection is inconsistent with actual internal selection.</td>
<td>Type-Defect, Target-0.34, Priority-Medium, Usability</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=767">Issue 767</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Pasting to tag pastes also to grid</td>
<td>Type-Defect, Priority-Medium, Target-0.34, OS-Linux</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=769">Issue 769</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Insert rows when multiple rows are selected adds rows between selected rows </td>
<td>Type-Defect, Priority-Medium, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=770">Issue 770</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Pasting non-ASCII characters works only if system encoding is UTF-8 (i.e. not on Windows)</td>
<td>Type-Defect, Priority-Medium, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=738">Issue 738</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Find Usages should go first through the current file</td>
<td>Type-Enhancement, Target-0.34, Usability, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=758">Issue 758</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Right click should select row/cell if it is not already selected</td>
<td>Type-Enhancement, Priority-Medium, Target-0.34, Usability</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=660">Issue 660</a></td>
<td>Defect</td>
<td>Low</td>
<td>Clicking tree when release notes is shown causes traceback</td>
<td>Type-Defect, Priority-Low, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=763">Issue 763</a></td>
<td>Defect</td>
<td>Low</td>
<td>Preview print does not support unicode</td>
<td>Type-Defect, Priority-Low, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=766">Issue 766</a></td>
<td>Defect</td>
<td>Low</td>
<td>Preview produces stack trace when no data is open</td>
<td>Type-Defect, Priority-Low, Target-0.34</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=772">Issue 772</a></td>
<td>Defect</td>
<td>Low</td>
<td>Navigating to keywords and testcases in html preview is broken </td>
<td>Type-Defect, Priority-Low, Target-0.34, Usability</td>
</tr>
</table>
<p>Altogether 27 issues.</p>
"""
