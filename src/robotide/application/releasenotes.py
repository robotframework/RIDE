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
<h2>Release notes for 0.33</h2>
<table border="1">
<tr>
<td><b>ID</b></td>
<td><b>Type</b></td>
<td><b>Priority</b></td>
<td><b>Summary</b></td>
<td><b>AllLabels</b></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=692">Issue 692</a></td>
<td>Defect</td>
<td>High</td>
<td>Open Directory dialog losts focus on Windows</td>
<td>Type-Defect, Priority-High, Target-0.33, OS-Windows, Usability</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=705">Issue 705</a></td>
<td>Defect</td>
<td>High</td>
<td>test runner plugin fails on windows if cwd is root (C:\, D:\, etc)</td>
<td>Type-Defect, Priority-High, OS-Windows, Target-0.33</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=718">Issue 718</a></td>
<td>Defect</td>
<td>High</td>
<td>Added keyword is not shown immediately</td>
<td>Type-Defect, Priority-High, Target-0.33</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=510">Issue 510</a></td>
<td>Enhancement</td>
<td>High</td>
<td>Show all tags of a test case</td>
<td>Type-Enhancement, Priority-High, Target-0.33</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=669">Issue 669</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Ride cannot be used on small screen</td>
<td>Type-Defect, Priority-Medium, Target-0.33</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=690">Issue 690</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Tooltip shown above other applications</td>
<td>Type-Defect, Priority-Medium, Target-0.33</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=698">Issue 698</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Removing individually selected lines does not work correctly</td>
<td>Type-Defect, Priority-Medium, Target-0.33</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=704">Issue 704</a></td>
<td>Defect</td>
<td>Medium</td>
<td>A case where delete cells undo fails</td>
<td>Type-Defect, Priority-Medium, Target-0.33</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=710">Issue 710</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Duplicate modification in RIDE 0.32 if multiple keywords have same name</td>
<td>Type-Defect, Priority-Medium, Target-0.33</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=715">Issue 715</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Test Runner causes trace at startup</td>
<td>Type-Defect, Priority-Medium, OS-OSX, Target-0.33</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=722">Issue 722</a></td>
<td>Defect</td>
<td>Medium</td>
<td>User keyword and Test case names are not HTML escaped when serialized</td>
<td>Type-Defect, Target-0.33, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=724">Issue 724</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Resource flickering during suite open</td>
<td>Type-Defect, Target-0.33, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=726">Issue 726</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Importing library with second last argument other than string type fails</td>
<td>Type-Defect, Priority-Medium, Target-0.33</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=694">Issue 694</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Individual tag is hard to find from long list of tags</td>
<td>Type-Enhancement, Priority-Medium, Target-0.33, Usability</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=695">Issue 695</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Editing tags is hard when there is lot of tags</td>
<td>Type-Enhancement, Priority-Medium, Target-0.33, Usability</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=701">Issue 701</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Ability to print test suite at preview</td>
<td>Type-Enhancement, Target-0.33, Priority-Medium</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=708">Issue 708</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>make settings iterable</td>
<td>Type-Enhancement, Priority-Medium, Target-0.33</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=691">Issue 691</a></td>
<td>Documentation</td>
<td>Medium</td>
<td>Embedded images are not loaded when too old wxpython version</td>
<td>Type-Documentation, Priority-Medium, Target-0.33</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=709">Issue 709</a></td>
<td>Documentation</td>
<td>Medium</td>
<td>Document with wxPython 2.8.10.1 in Windows 7 Argument, Timeout and Return Value Dialog are opened twice</td>
<td>Type-Documentation, Priority-Medium, Target-0.33</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=700">Issue 700</a></td>
<td>Defect</td>
<td>Low</td>
<td>Delete shortcut is not working on Delete Rows</td>
<td>Type-Defect, Priority-Low, Target-0.33</td>
</tr>
</table>
<p>Altogether 20 issues.</p>
"""
