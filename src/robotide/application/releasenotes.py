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
<h2>Release notes for 0.28</h2>
<table border="1">
<tr>
<td><b>ID</b></td>
<td><b>Type</b></td>
<td><b>Priority</b></td>
<td><b>Summary</b></td>
<td><b>AllLabels</b></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=525">Issue 525</a></td>
<td>Defect</td>
<td>High</td>
<td>Default Tags not anymore visible in RIDE editor</td>
<td>Type-Defect, Priority-High, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=13">Issue 13</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Create a new user keyword from value in test case or user keyword editor</td>
<td>Type-Enhancement, Priority-High, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=250">Issue 250</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Extract keyword refactoring</td>
<td>Type-Enhancement, Priority-High, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=255">Issue 255</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Internal logging facility</td>
<td>Type-Enhancement, Priority-High, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=526">Issue 526</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Add support for writing pipe separator in txt file format</td>
<td>Type-Enhancement, Priority-High, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=208">Issue 208</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Selecting with mouse from keyword completion list does not work in Windows</td>
<td>Type-Defect, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=266">Issue 266</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Variable completion should support also user keyword arguments</td>
<td>Type-Defect, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=297">Issue 297</a></td>
<td>Defect</td>
<td>Medium</td>
<td>New Test Case and New User Keyword dialogs have poor initial position</td>
<td>Type-Defect, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=480">Issue 480</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Inplace Templates</td>
<td>Type-Defect, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=506">Issue 506</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Traceback when clicking in the Suite options</td>
<td>Type-Defect, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=513">Issue 513</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Alternative `Ctrl-Alt-Space` shortcut for keyword completion is not visible</td>
<td>Type-Defect, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=514">Issue 514</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Mouse over setting fields steals focus from keyword search</td>
<td>Type-Defect, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=515">Issue 515</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Variables from variable files are not available when parsing resource imports</td>
<td>Type-Defect, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=520">Issue 520</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Colorization of keywords from xml library specs does not work</td>
<td>Type-Defect, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=524">Issue 524</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Executing a run configuration that has no command causes the output tab to be uncloseable</td>
<td>Target-0.28, Type-Defect, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=528">Issue 528</a></td>
<td>Defect</td>
<td>Medium</td>
<td>If variable in variable table has unresolvable variables in value, the variable is not added to content asistance list</td>
<td>Type-Defect, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=529">Issue 529</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Variables are shown to be always from current file</td>
<td>Type-Defect, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=530">Issue 530</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Clearing settings does not clear comments</td>
<td>Type-Defect, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=546">Issue 546</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Dialogs are always shown on the primary monitor on Windows</td>
<td>Type-Defect, Priority-Medium, Target-0.28, OS-Windows</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=549">Issue 549</a></td>
<td>Defect</td>
<td>Medium</td>
<td>\n in test data is serialized to html with extra newline and space</td>
<td>Type-Defect, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=37">Issue 37</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Moving to user keyword definition from keyword search dialog</td>
<td>Type-Enhancement, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=517">Issue 517</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>`Create new user keyword` -dialog should allow entering also arguments</td>
<td>Type-Enhancement, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=518">Issue 518</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Shortcuts for moving list control items up and down</td>
<td>Type-Enhancement, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=522">Issue 522</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>RIDE should higlight/jump to keywords using the Given/When/And/Then grammar</td>
<td>Type-Enhancement, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=537">Issue 537</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Selecting rows from row number header does not auto-scroll</td>
<td>Target-0.28, Type-Enhancement, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=538">Issue 538</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Select all cells in grid</td>
<td>Priority-Medium, Target-0.28, Type-Enhancement</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=544">Issue 544</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Add all builtin variables to variable completion</td>
<td>Type-Enhancement, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=547">Issue 547</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Add `F5` shortcut to `Search Keywords` and `F6` to `Preview`</td>
<td>Type-Enhancement, Priority-Medium, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=548">Issue 548</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Support all available formats in `Preview`</td>
<td>Priority-Medium, Type-Enhancement, Target-0.28</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=508">Issue 508</a></td>
<td>Documentation</td>
<td>Medium</td>
<td>Windows installer puts wrong Python path in ride.py</td>
<td>Type-Documentation, Target-0.28, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=354">Issue 354</a></td>
<td>Defect</td>
<td>Low</td>
<td>Alt-Right and Alt-Left does not work on Linux, replace with Alt-Z, Alt-X</td>
<td>Priority-Low, Type-Defect, Target-0.28</td>
</tr>
</table>
<p>Altogether 31 issues.</p>
"""
