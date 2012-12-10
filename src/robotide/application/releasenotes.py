#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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
from robotide.pluginapi import ActionInfo


class ReleaseNotes(object):
    """Shows release notes of the current version.

    The release notes tab will automatically be shown once per release.
    The user can also view them on demand by selecting "Release Notes"
    from the help menu.
    """

    def __init__(self, application):
        self.application = application
        settings =  application.settings
        self.version_shown = settings.get('version_shown', '')
        self._view = None
        self.enable()

    def enable(self):
        self.application.frame.actions.register_action(ActionInfo('Help', 'Release Notes', self.show,
                                        doc='Show the release notes'))
        self.show_if_updated()

    def show_if_updated(self):
        if self.version_shown != VERSION:
            self.show()
            self.application.settings['version_shown'] = VERSION

    def show(self, event=None):
        if not self._view:
            self._view = self._create_view()
            self.application.frame.notebook.AddPage(self._view, "Release Notes", select=False)
        self.application.frame.notebook.show_tab(self._view)

    def bring_to_front(self):
        if self._view:
            self.application.frame.notebook.show_tab(self._view)

    def _create_view(self):
        panel = wx.Panel(self.application.frame.notebook)
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
  <li><a href="https://github.com/robotframework/RIDE">
      RIDE project page on github</a></li>
  <li><a href="https://github.com/robotframework/RIDE/wiki/Installation-Instructions">
      Installation instructions</a></li>
  <li><a href="https://github.com/robotframework/RIDE/wiki/Release-notes">
      Release notes</a></li>
</ul>
""" % VERSION

# *** DO NOT EDIT THE CODE BELOW MANUALLY ***
# Release notes are updated automatically by package.py script whenever
# a numbered distribution is created.
RELEASE_NOTES = """
<h2>Release notes for 0.54</h2>
<table border="1">
<tr>
<td><p><b>ID</b></p></td>
<td><p><b>Type</b></p></td>
<td><p><b>Priority</b></p></td>
<td><p><b>Summary</b></p></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=32">Issue 32</a></td>
<td>Enhancement</td>
<td>Critical</td>
<td>Searching tests using name, documentation or tags</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1124">Issue 1124</a></td>
<td>Defect</td>
<td>High</td>
<td>Font size displayed does not match font size set</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1131">Issue 1131</a></td>
<td>Defect</td>
<td>High</td>
<td>Multiline documentation should be formatted in multiple rows</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1141">Issue 1141</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Document and notify at start-up that wxPython 2.8.12.1 is the minimum supported version</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1004">Issue 1004</a></td>
<td>Defect</td>
<td>Medium</td>
<td>popup help interferes with editing/copying/pasting of cells</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1064">Issue 1064</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Directory init file library imports fail on linux</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1080">Issue 1080</a></td>
<td>Defect</td>
<td>Medium</td>
<td>'Find Where Used' on for variable name with dashes excludes items after the dash</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1092">Issue 1092</a></td>
<td>Defect</td>
<td>Medium</td>
<td>"File Changed On Disk" keeps poping up repeatedly even after a deleted suite has been removed from the project</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1101">Issue 1101</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Green Dot Indication Isn't Visible for tests' with '.'</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1110">Issue 1110</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Ride crashes regularly in Ubuntu 12.04</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1118">Issue 1118</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Using tab character in text editor does not work</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1119">Issue 1119</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Deleting resource file and imports throws an exception</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1122">Issue 1122</a></td>
<td>Defect</td>
<td>Medium</td>
<td>RIDE Preferences Dialog shows 40 spaces, should be 4</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1138">Issue 1138</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Hot key "Control + A" does not work under windows os</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1144">Issue 1144</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Failures in importing libraries (e.g. `Remote` library) can hang RIDE</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=198">Issue 198</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Ride should have links to help documents in the "Help"  menu.</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1121">Issue 1121</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Add keyword search to toolbar</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1132">Issue 1132</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Installer should optionally create shortcuts on windows</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1133">Issue 1133</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Installer should check that wx exists</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1026">Issue 1026</a></td>
<td>Defect</td>
<td>Low</td>
<td>Pressing Ctrl+D when cell editor open will remove two rows in Linux</td>
</tr>
</table>
<p>Altogether 20 issues.</p>
"""
