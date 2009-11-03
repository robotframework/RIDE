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

"""Release notes plugin

This will create a notebook tab that displays release notes

The release notes tab will automatically be shown once per release.
The user can also view them on demand by selecting "Release Notes"
from the help menu.
"""

import wx
from plugin import Plugin
from robotide.version import VERSION
from wx.lib.ClickableHtmlWindow import PyClickableHtmlWindow


class ReleaseNotesPlugin(Plugin):

    """Display Release Notes in a Tab"""
    persistent_attributes = {'version_shown':''}

    def __init__(self, application):
        Plugin.__init__(self, application, initially_active=True)
        self._panel = None

    def activate(self):
        self._id = self.add_to_menu('Release Notes', 'Show the release notes',
                                    self.OnShowReleaseNotes, 'Help')
        self.auto_show()

    def deactivate(self):
        self.remove_from_menu('Help', self._id)

    def auto_show(self):
        """Show the release notes if the current version release notes haven't been shown."""
        if self.version_shown != VERSION:
            self.show()
            self.version_shown = VERSION #Saves shown version

    def show(self):
        """Show the release notes tab"""
        if not self._panel:
            self._create_page()
        self.show_page(self._panel)

    def OnShowReleaseNotes(self, event):
        """Callback for the Release Notes menu item"""
        self.show()

    def _create_page(self):
        """Add a tab for this plugin to the notebook"""
        notebook = self.get_notebook()
        if notebook:
            self._panel = wx.Panel(notebook)
            self.html = PyClickableHtmlWindow(self._panel, wx.ID_ANY)
            self.html.SetStandardFonts()
            self.html.SetPage(WELCOME_TEXT + RELEASE_NOTES)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(self.html, 1, wx.EXPAND|wx.ALL, border=8)
            self._panel.SetSizer(sizer)
            notebook.AddPage(self._panel, "Release Notes", select=False)


WELCOME_TEXT = """
<h2>Welcome to use RIDE version %s</h2>

<p>Thank you for using the Robot Framework IDE (RIDE).</p>

<p>Visit RIDE on the web:</p>

<ul>
  <li><a href="http://code.google.com/p/robotframework-ride/">
      RIDE project page on Google Code</a></li>
  <li><a href="http://code.google.com/p/robotframework-ride/wiki/InstallationInstruction">
      Installation instructions</a></li>
  <li><a href="http://code.google.com/p/robotframework-ride/wiki/ReleaseNotes">
      Release notes</a></li>
</ul>
""" % VERSION

# *** DO NOT EDIT THE CODE BELOW MANUALLY ***
# Release notes are updated automatically by package.py script whenever
# a numbered distribution is created.
RELEASE_NOTES = ""
