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
<h2>Release notes for 0.27</h2>
<table border="1">
<tr>
<td><b>ID</b></td>
<td><b>Type</b></td>
<td><b>Priority</b></td>
<td><b>Summary</b></td>
<td><b>AllLabels</b></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=490">Issue 490</a></td>
<td>Defect</td>
<td>High</td>
<td>RIDE does not handle circular resource imports</td>
<td>Priority-High, Type-Defect, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=295">Issue 295</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Resource name doesn't accept non-ascii characters</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=418">Issue 418</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Recent files not updated when format was changed</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=430">Issue 430</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Preview does not show added user keyword or test immediately</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=434">Issue 434</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Documentation popup is not destroyed if cursor is outside RIDE window</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=438">Issue 438</a></td>
<td>Defect</td>
<td>Medium</td>
<td>When a Test Suite references a Remote library that is not present RIDE gets painfully slow</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=440">Issue 440</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Auto-Completion pop-up is fixed size and can go beyond physical screen boundaries</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=441">Issue 441</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Use OSX keys instead of CTRL keys for editing</td>
<td>Type-Defect, Priority-Medium, OS-OSX, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=443">Issue 443</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Keyboard shortcuts do not work on Linux when mouse is over cells with help boxes</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=445">Issue 445</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Uncomment Rows causes empty cell</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=447">Issue 447</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Using CMD-<arrow keys> doesn't work</td>
<td>Type-Defect, Priority-Medium, OS-OSX, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=485">Issue 485</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Spaces in path of imported files are removed when creating LibrarySpec object thus not finding the file.</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=491">Issue 491</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Move up or down causing error in console</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=492">Issue 492</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Grid needs to be recolorized after insert/delete cells</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=495">Issue 495</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Content in list variable editor cells does not wrap correctly</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=497">Issue 497</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Copy test does not initialize setup / teardown / etc fields properly</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=500">Issue 500</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Moving edited items in 'Manage Run Configurations'  loses data</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=501">Issue 501</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Changes done via 'Manage Run Configurations' are not taken in use if the configuration is rerun from 'Run Again' button</td>
<td>Type-Defect, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=280">Issue 280</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Allow navigation to setup/teardown keywords</td>
<td>Type-Enhancement, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=435">Issue 435</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td> Search keywords should give prefix-match higher priority</td>
<td>Type-Enhancement, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=471">Issue 471</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Controls for documentation and setup/teardown should have informative tooltip</td>
<td>Type-Enhancement, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=472">Issue 472</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>It should be possible to configure number of columns in list variable dialog</td>
<td>Type-Enhancement, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=473">Issue 473</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Stretching list variable window should also stretch the table inside it</td>
<td>Type-Enhancement, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=479">Issue 479</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>RIDE cell selection behaviour inconsistent for top left cell</td>
<td>Type-Enhancement, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=488">Issue 488</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>`${/}` variable does not work</td>
<td>Type-Enhancement, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=489">Issue 489</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Inserting and deleting cells should work on ranges</td>
<td>Type-Enhancement, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=493">Issue 493</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>`Insert Cells` and `Delete Cells` menu items to list variable editor</td>
<td>Type-Enhancement, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=499">Issue 499</a></td>
<td>Documentation</td>
<td>Medium</td>
<td>Document where run configurations are stored</td>
<td>Type-Documentation, Priority-Medium, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=259">Issue 259</a></td>
<td>Defect</td>
<td>Low</td>
<td>Keywords with long keyword names (e.g. `BuiltIn.Log`) are not colorized</td>
<td>Type-Defect, Target-0.27, Priority-Low</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=285">Issue 285</a></td>
<td>Defect</td>
<td>Low</td>
<td>Inconsistent displaying of the RIDE output files in browser</td>
<td>Type-Defect, Priority-Low, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=425">Issue 425</a></td>
<td>Defect</td>
<td>Low</td>
<td>RIDE destroys/recreates editor when you select edit tab</td>
<td>Type-Defect, Priority-Low, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=486">Issue 486</a></td>
<td>Defect</td>
<td>Low</td>
<td>When RIDE 0.26 reports collision in scalar and list variable names, the error message is duplicated</td>
<td>Priority-Low, Type-Defect, Target-0.27</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=484">Issue 484</a></td>
<td>Enhancement</td>
<td>Low</td>
<td>`Insert cell` and `Delete cell` buttons should be moved to context menu and `Add row` and `Add column` buttons removed</td>
<td>Type-Enhancement, Priority-Low, Target-0.27</td>
</tr>
</table>
<p>Altogether 33 issues.</p>
"""
