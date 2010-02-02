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
<h2>Release notes for 0.21</h2>
<table border="1">
<tr>
<td><b>ID</b></td>
<td><b>Type</b></td>
<td><b>Priority</b></td>
<td><b>Summary</b></td>
<td><b>AllLabels</b></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=270">Issue 270</a></td>
<td>Defect</td>
<td>High</td>
<td>Search Keywords jams RIDE and Python takes all CPU time with big test data</td>
<td>Type-Defect, Priority-High, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=318">Issue 318</a></td>
<td>Defect</td>
<td>High</td>
<td>Undo problem</td>
<td>Type-Defect, Priority-High, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=341">Issue 341</a></td>
<td>Defect</td>
<td>High</td>
<td>Only first resource import of a resource file is processed</td>
<td>Type-Defect, Priority-High, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=253">Issue 253</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Generic plugin for running any command in the system</td>
<td>Type-Enhancement, Priority-High, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=357">Issue 357</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Do not create all test/keyword tree nodes when suite is loaded to save memory</td>
<td>Type-Enhancement, Priority-High, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=256">Issue 256</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Variables in library imports are not resolved</td>
<td>Type-Defect, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=276">Issue 276</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Test case and user keyword copy operation takes very long time to process after 10-15 copies</td>
<td>Type-Defect, Priority-Medium, Target-0.21, Performance</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=286">Issue 286</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Changing character's case in test case name causes validation error</td>
<td>Type-Defect, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=304">Issue 304</a></td>
<td>Defect</td>
<td>Medium</td>
<td>error found when opening directory</td>
<td>Type-Defect, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=317">Issue 317</a></td>
<td>Defect</td>
<td>Medium</td>
<td>RIDE crashes if user keyword data contains UserErrorHandlers</td>
<td>Type-Defect, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=348">Issue 348</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Copied test case's or keyword's settings cannot be edited </td>
<td>Type-Defect, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=349">Issue 349</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Keyword is not completed when pressing CTRL-Space in an empty cell</td>
<td>Type-Defect, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=356">Issue 356</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Some data crashes RIDE when editors are created</td>
<td>Type-Defect, Target-0.21, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=362">Issue 362</a></td>
<td>Defect</td>
<td>Medium</td>
<td>RIDE crashes when selecting another file from the recent files</td>
<td>Type-Defect, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=364">Issue 364</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Documentation popup should not appear when the window doesn't have focus (Linux)</td>
<td>Type-Defect, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=218">Issue 218</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Give access of other available plugins to a plugin that is to be activated</td>
<td>Type-Enhancement, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=266">Issue 266</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Variable completion should support also user keyword arguments</td>
<td>Type-Enhancement, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=281">Issue 281</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Content assist should be extensible</td>
<td>Type-Enhancement, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=322">Issue 322</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Show progress bar when loading test data</td>
<td>Type-Enhancement, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=327">Issue 327</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>List variable editor should use grid instead of single input field</td>
<td>Type-Enhancement, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=328">Issue 328</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Collect all test data parsing errors into one dialog</td>
<td>Type-Enhancement, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=333">Issue 333</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Keyword colors</td>
<td>Type-Enhancement, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=351">Issue 351</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>`${/}` should be replaced with `/` in import related settings automatically</td>
<td>Type-Enhancement, Priority-Medium, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=273">Issue 273</a></td>
<td>Defect</td>
<td>Low</td>
<td>Changing format recursively does not work with directories without __init__ file</td>
<td>Type-Defect, Priority-Low, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=278">Issue 278</a></td>
<td>Defect</td>
<td>Low</td>
<td>Resource file name not shown correctly in the left-hand side tree</td>
<td>Type-Defect, Priority-Low, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=283">Issue 283</a></td>
<td>Defect</td>
<td>Low</td>
<td>RIDE keyword search result doesn't display html tables correctly</td>
<td>Type-Defect, Priority-Low, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=284">Issue 284</a></td>
<td>Defect</td>
<td>Low</td>
<td>Libraries are found from spec files case insensitively in Windows</td>
<td>Type-Defect, Priority-Low, Target-0.21</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=336">Issue 336</a></td>
<td>Enhancement</td>
<td>Low</td>
<td>'save all' button needed</td>
<td>Type-Enhancement, Priority-Low, Target-0.21</td>
</tr>
</table>
<p>Altogether 28 issues.</p>
"""
