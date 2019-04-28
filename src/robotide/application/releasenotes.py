#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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

<p>Thank you for using the <a href="https://robotframework.org/">Robot Framework</a> IDE (RIDE).</p>

<p>Visit RIDE on the web:</p>

<ul>
  <li><a href="https://github.com/robotframework/RIDE">
      RIDE project page on github</a></li>
  <li><a href="https://github.com/robotframework/RIDE/wiki/Installation-Instructions">
      Installation instructions</a></li>
  <li><a href="https://github.com/robotframework/RIDE/releases">
      Release notes</a></li>
</ul>
""" % VERSION

# *** DO NOT EDIT THE CODE BELOW MANUALLY ***
# Release notes are updated automatically by package.py script whenever
# a numbered distribution is created.
RELEASE_NOTES = """
<h1>Robot Framework IDE 1.7.4</h1>
<p><a href="https://github.com/robotframework/RIDE/">RIDE (Robot Framework IDE)</a> 1.7.4 is a new release with major enhancements
and bug fixes. This version 1.7.4 includes fixes for installer and new File explorer.</br>
The reference for valid arguments is <a href="http://robotframework.org" rel="nofollow">Robot Framework</a> version 3.1.1.</p>
<h2>The most notable enhancements (from version 1.7.3.1) are:</h2>
<ul>
<li>Compatible with Python 2.7 and &gt;=3.6</li>
<li>Runs with "any" wxPython version (2.8.12.1, 3.0.2 on Python 2.7)
and 4.0.4 for both Python 2.7 and &gt;=3.6</li>
<li>Runner can select new or old versions of Robot Framework (<code>pybot</code> vs <code>robot</code>)</li>
<li>Panes, Tabs, Toolbar are detachable and re-positionable thanks to wxPython's AUI module</li>
<li>Text Editor now have a autocomplete feature</li>
<li>Test cases on tree pane, have the new official icon, and is animated when running or paused</li>
<li>Long test names on tree pane, have name shortened by ... and name visible on tool-tip</li>
<li>On tree pane at test suite level, context menu allows to open folder in file manager,
and to remove the Read-Only file attribute</li>
<li>If no tests are selected there will be a confirmation to proceed with running all tests</li>
<li>Like F8 to run tests, now there is F9 to run them with log level DEBUG</li>
<li>The Grid Editor now have a JSON editor for a cell (it validates when saving)</li>
</ul>
<h2>The most notable enhancements (from version 1.7.4) are:</h2>
<ul>
<li>This is the <b>last version supporting Python 2.7</b>.</li>
<li>A new File Explorer allows to open supported file types in RIDE, or other types in a basic code editor. To open a file you must double-click on it.
If it is a supported file format but not with the correct structure (for example a resource file), an error message is shown, and then opens in code editor.</li>
<li>On Grid Editor, the cells can be autoajusting with wordwrap. There is a new checkbox in Tools>Preferences>Grid Editor.</li>
<li>Pressing the Ctrl on the Grid Editor, when over a keyword it will show its documentation (that can be detached with mouse click).</li>


<a name="user-content-unfortunately-this-release-may-introduce-new-bugs-unknown-or-known-like-the-ones"></a>
<h3><a id="user-content-unfortunately-this-release-may-introduce-new-bugs-unknown-or-known-like-the-ones" class="anchor" aria-hidden="true" href="#unfortunately-this-release-may-introduce-new-bugs-unknown-or-known-like-the-ones"><svg class="octicon octicon-link" viewBox="0 0 16 16" version="1.1" width="16" height="16" aria-hidden="true"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>Unfortunately, this release may introduce new bugs, unknown or known like the ones:</h3>
<ul>
<li>On Windows to call autocomplete in Grid Editor, you have to use Ctrl-Alt-Space, (or keep using Ctrl-Space after disabling Text Editor)</li>
<li>On MacOS to call autocomplete in Grid Editor, you have to use Alt-Space</li>
<li>On Linux to call autocomplete in Grid Editor, you have to use Ctrl-Space</li>
<li>On Windows 10, in Grid Editor, when you select text on a cell, the selection, although valid, is not visible</li>
<li>On some Linuxes (Fedora 28, for example), when you click No in some Dialog boxes, there is the repetition of those Dialogs</li>
<li>On some Linuxes the new validation of test suites, may complaint about HTML format, and this makes not opening the folders. You have to select a single file, kill RIDE and restart it.</li>
</ul>
<p>(and more for you to find out ;) )</p>
<p>All issues targeted for RIDE v1.7.4 can be found
from the <a href="https://github.com/robotframework/RIDE/issues?q=milestone%3Av1.7.4">issue tracker milestone</a>.</p>
<p>Questions and comments related to the release can be sent to the
<a href="http://groups.google.com/group/robotframework-users" rel="nofollow">robotframework-users</a> mailing list or to the channel #ride on
<a href="https://robotframework-slack-invite.herokuapp.com" rel="nofollow">Robot Framework Slack</a>, and possible bugs submitted to the <a href="https://github.com/robotframework/RIDE/issues">issue tracker</a>.</p>
<p>If you have <a href="http://pip-installer.org" rel="nofollow">pip</a> installed, just run</p>
<div class="highlight highlight-text-roff"><pre>pip install --upgrade robotframework-ride</pre></div>
<p>to install (or upgrade) the latest available release or use</p>
<div class="highlight highlight-text-roff"><pre>pip install robotframework-ride==1.7.4</pre></div>
<p>to install exactly this version. Alternatively you can download the source
distribution from <a href="https://pypi.python.org/pypi/robotframework-ride" rel="nofollow">PyPI</a> and install it manually. You may want to see the
document <a href="https://github.com/robotframework/RIDE/blob/master/BUILD.rest">BUILD.rest</a> for other details.</p>
<p>RIDE 1.7.4a1 was released on Sunday April 28, 2019.</p>


<h4>Full list of fixes and enhancements</h4>
<table border="1">


<thead valign="bottom">
<tr><th>ID</th>
<th>Type</th>
<th>Priority</th>
<th>Summary</th>
</tr>
</thead>
<tbody valign="top">
<tr></tr>
</tbody>
</table>
<p>Altogether 23 issues. View on the <a href="https://github.com/robotframework/RIDE/issues?q=milestone%3Av1.7.4">issue tracker</a>.</p>

"""
