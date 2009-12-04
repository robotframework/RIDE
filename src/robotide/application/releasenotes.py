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
<h2>Release notes for 0.20</h2>
<table border="1">
<tr>
<td><b>ID</b></td>
<td><b>Type</b></td>
<td><b>Priority</b></td>
<td><b>Summary</b></td>
<td><b>AllLabels</b></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=254">Issue 254</a></td>
<td>Enhancement</td>
<td>Critical</td>
<td>Plugin API review and enhancements</td>
<td>Type-Enhancement, Priority-Critical, Target-0.20</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=212">Issue 212</a></td>
<td>Defect</td>
<td>High</td>
<td>Key bindings (e.g. ctrl-c) are tied to main editor window and cannot be used by plugins</td>
<td>Type-Defect, Priority-High, Usability, Target-0.20</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=289">Issue 289</a></td>
<td>Defect</td>
<td>High</td>
<td>Adding a new suite saves the file into wrong dir.</td>
<td>Type-Defect, Priority-High, Target-0.20</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=331">Issue 331</a></td>
<td>Defect</td>
<td>High</td>
<td>Memory leak when changing editors</td>
<td>Type-Defect, Priority-High, Target-0.20</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=252">Issue 252</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Implement default test suite, test case, and keyword editors as plugin</td>
<td>Type-Enhancement, Priority-High, Target-0.20</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=296">Issue 296</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Remove broken unneccessary Save as... functionality</td>
<td>Type-Enhancement, Priority-High, Target-0.20</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=207">Issue 207</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Editors should not have two horizontal scrollbars</td>
<td>Type-Defect, Priority-Medium, Target-0.20</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=275">Issue 275</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Publisher should catch error in message handlers.</td>
<td>Type-Defect, Priority-Medium, Target-0.20</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=329">Issue 329</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Pressing delete key in test case name deletes from test step table</td>
<td>Type-Defect, Priority-Medium, Target-0.20</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=240">Issue 240</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>It should be possible to deactivate the Preview plugin </td>
<td>Type-Enhancement, Priority-Medium, Target-0.20</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=313">Issue 313</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Context menu to the editor to support copy, paste, etc.</td>
<td>Type-Enhancement, Priority-Medium, Target-0.20</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=287">Issue 287</a></td>
<td>Defect</td>
<td>Low</td>
<td>Clicking suite name goes to rename mode in Windows</td>
<td>Type-Defect, Priority-Low, Target-0.20</td>
</tr>
</table>
<p>Altogether 12 issues.</p>
"""
