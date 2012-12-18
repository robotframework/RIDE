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
<h2>Release notes for 0.55</h2>
<table border="1">
<tr>
<td><p><b>ID</b></p></td>
<td><p><b>Type</b></p></td>
<td><p><b>Priority</b></p></td>
<td><p><b>Summary</b></p></td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1135">Issue 1135</a></td>
<td>Defect</td>
<td>High</td>
<td>Backwards going resource imports sometimes fail (Are shown in red color and resources are shown as unused)</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1155">Issue 1155</a></td>
<td>Defect</td>
<td>High</td>
<td>"Search" button of "Search Tests" dialog does nothing</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1164">Issue 1164</a></td>
<td>Defect</td>
<td>High</td>
<td>Renaming keyword with embedded arguments fails</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1147">Issue 1147</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Screenshot library prevents RIDE from closing completely</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1154">Issue 1154</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Search Keywords get error and never stops refreshing the screen</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1157">Issue 1157</a></td>
<td>Defect</td>
<td>Medium</td>
<td>HTML format change does not work</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1159">Issue 1159</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Comments are not handled correctly in FOR loops</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1160">Issue 1160</a></td>
<td>Defect</td>
<td>Medium</td>
<td>enabling/disabling plugins does not work</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1161">Issue 1161</a></td>
<td>Defect</td>
<td>Medium</td>
<td>RIDE freezes w/ 'DocumentationController' object has no attribute 'replace_keyword'</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1162">Issue 1162</a></td>
<td>Defect</td>
<td>Medium</td>
<td>Editing in text editor is not possible if there is a comment starting with two hash characters</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1166">Issue 1166</a></td>
<td>Defect</td>
<td>Medium</td>
<td>For loop header row move throws an exception</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1117">Issue 1117</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Support wildcards in excludes</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1137">Issue 1137</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Clean-up menus, toolbars, etc.</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1150">Issue 1150</a></td>
<td>Enhancement</td>
<td>Medium</td>
<td>Excludes editable in Preferences</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1146">Issue 1146</a></td>
<td>Defect</td>
<td>Low</td>
<td>global variable value set problem</td>
</tr>
<tr>
<td><a href="http://code.google.com/p/robotframework-ride/issues/detail?id=1167">Issue 1167</a></td>
<td>Defect</td>
<td>Low</td>
<td>Test suite files starting with underscore cause parse error</td>
</tr>
</table>
<p>Altogether 16 issues.</p>
"""
