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
<h2>Release notes for 0.31</h2>
<table border="1">
<tr>
<td><b>ID</b></td>
<td><b>Type</b></td>
<td><b>Priority</b></td>
<td><b>Summary</b></td>
<td><b>AllLabels</b></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=15">Issue 15</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Argument count check for keywords</td>
<td>Type-Enhancement, Priority-High, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=558">Issue 558</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Find places where user keyword has been used</td>
<td>Priority-High, Type-Enhancement, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=595">Issue 595</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Highlight occurrences on grid editor</td>
<td>Type-Enhancement, Priority-High, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=649">Issue 649</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Put RIDE to PyPI to allow installation with `easy_install`</td>
<td>Type-Enhancement, Priority-High, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=612">Issue 612</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Location of keywords in tree is changed if directory suite is reloaded</td>
<td>Type-Defect, Priority-Medium, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=613">Issue 613</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Ctrl-s does not save the file after keyword arguments are modified</td>
<td>Type-Defect, Priority-Medium, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=627">Issue 627</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Edited variables are not correctly updated in the tree</td>
<td>Type-Defect, Priority-Medium, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=628">Issue 628</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Autocomplete does not show long keyword names fully</td>
<td>Type-Defect, Usability, Priority-Medium, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=630">Issue 630</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Repeated CTRL+Space slows down autocompletion</td>
<td>Type-Defect, Priority-Medium, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=631">Issue 631</a></td>
<td>Defect</td>
<td>Medium</td>
<td>First click in table selects always cell in row 1, column 1</td>
<td>Type-Defect, Priority-Medium, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=632">Issue 632</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Setups and teardown links are not updated in suite if imports are changed</td>
<td>Type-Defect, Priority-Medium, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=637">Issue 637</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Selection is not visible after deleting item on Import/Variable/Metadata editors</td>
<td>Type-Defect, Priority-Medium, Target-0.31, Usability</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=639">Issue 639</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Selecting last variable from the tree and deleting it causes an error</td>
<td>Type-Defect, Priority-Medium, Target-0.31, OS-Windows</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=640">Issue 640</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Renaming or deleting a test case file inside directory does not work</td>
<td>Type-Defect, Priority-Medium, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=651">Issue 651</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Resources should be reloaded when opening a new project</td>
<td>Type-Defect, Target-0.31, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=654">Issue 654</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Typing $ or @ in the content assist closes it on Windows</td>
<td>Type-Defect, Priority-Medium, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=339">Issue 339</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Show error when importing library fails</td>
<td>Type-Enhancement, Priority-Medium, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=550">Issue 550</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Embedded Arguments in Keywords should be supported</td>
<td>Type-Enhancement, Priority-Medium, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=592">Issue 592</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Show argument name in tooltip when hovering over an argument</td>
<td>Type-Enhancement, Priority-Medium, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=599">Issue 599</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Documentation popup should be detachable</td>
<td>Type-Enhancement, Priority-Medium, Target-0.31</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=638">Issue 638</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Removing variables should be easier</td>
<td>Type-Enhancement, Priority-Medium, Target-0.31, Usability</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=656">Issue 656</a></td>
<td>Defect</td>
<td>Low</td>
<td>When deleting rows the same row numbers are selected afterwards</td>
<td>Type-Defect, Priority-Low, Target-0.31</td>
</tr>
</table>
<p>Altogether 22 issues.</p>
"""
