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
<h2>Release notes for 0.35</h2>
<table border="1">
<tr>
<td><b>ID</b></td>
<td><b>Type</b></td>
<td><b>Priority</b></td>
<td><b>Summary</b></td>
<td><b>AllLabels</b></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=787">Issue 787</a></td>
<td>Defect</td>
<td>High</td>
<td>Multiple tags copy</td>
<td>Type-Defect, Target-0.35, Priority-High</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=723">Issue 723</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Ampersands (&) are not shown in wx.StaticText components</td>
<td>Type-Defect, Priority-Medium, Target-0.35</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=765">Issue 765</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Cancel of saving directory file reports directory as saved</td>
<td>Type-Defect, Priority-Medium, Target-0.35</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=771">Issue 771</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Undo does not work after saving if data contains empty lines</td>
<td>Type-Defect, Priority-Medium, Target-0.35</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=773">Issue 773</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Keyword completion: Global variable shadows keyword argument</td>
<td>Type-Defect, Target-0.35, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=775">Issue 775</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Format change does not change source in file editor</td>
<td>Type-Defect, Priority-Medium, Target-0.35</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=782">Issue 782</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Comment and Uncomment from row header's context menu does not work on Linux</td>
<td>Type-Defect, Priority-Medium, Target-0.35, OS-Linux</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=783">Issue 783</a></td>
<td>Defect</td>
<td>Medium</td>
<td>AttributeError: 'MacRidePopupWindow' object has no attribute 'screen_position'</td>
<td>Type-Defect, Priority-Medium, Target-0.35</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=777">Issue 777</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Possibility to edit variable names from tree</td>
<td>Type-Enhancement, Target-0.35, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=784">Issue 784</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>When editing import, variable or metadata, selection is lost  </td>
<td>Type-Enhancement, Priority-Medium, Target-0.35, Usability</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=611">Issue 611</a></td>
<td>Defect</td>
<td>Low</td>
<td>Search plug-in (F3) does not immediately enable the "Search" button</td>
<td>Type-Defect, Priority-Low, Target-0.35</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=686">Issue 686</a></td>
<td>Defect</td>
<td>Low</td>
<td>Last item cannot be removed from Manage Run Configurations</td>
<td>Type-Defect, Priority-Low, Target-0.35</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=696">Issue 696</a></td>
<td>Defect</td>
<td>Low</td>
<td>End of suite's title and/or source are not visible</td>
<td>Type-Defect, Priority-Low, Target-0.35</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=774">Issue 774</a></td>
<td>Defect</td>
<td>Low</td>
<td>Search keyword dialog goes behind RIDE main window when find usages button is pressed</td>
<td>Type-Defect, Priority-Low, Target-0.35</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=788">Issue 788</a></td>
<td>Defect</td>
<td>Low</td>
<td>Syntax highlight does not recognize keywords with underscores in test data</td>
<td>Type-Defect, Priority-Low, Target-0.35</td>
</tr>
</table>
<p>Altogether 15 issues.</p>
"""
