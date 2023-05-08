# -*- encoding: utf-8 -*-
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

import os
import re
import time
import wx
from wx import Colour
from wx.lib.ClickableHtmlWindow import PyClickableHtmlWindow
from os.path import abspath, join, dirname

from ..action import ActionInfo
from ..version import VERSION
from ..widgets import HtmlDialog

HTML_FOREGROUND = 'foreground text'


class ReleaseNotes(object):
    """Shows release notes of the current version.

    The release notes tab will automatically be shown once per release.
    The user can also view them on demand by selecting "Release Notes"
    from the help menu.
    """

    def __init__(self, application):
        self.application = application
        settings = application.settings
        self.version_shown = settings.get('version_shown', '')
        self.general_settings = settings['General']
        self._view = None
        self._dialog = None
        self.enable()

    def enable(self):
        self.application.frame.actions.register_action(ActionInfo('Help', 'Release Notes',
                                                                  self.show,
                                                                  doc='Show the release notes'))
        self.application.frame.actions.register_action(ActionInfo('Help', 'Offline Change Log',
                                                                  self.show_changelog,
                                                                  doc='Show the offline CHANGELOG'))
        self.show_if_updated()

    def show_if_updated(self):
        if self.version_shown != VERSION:
            self.show()
            self.application.settings['version_shown'] = VERSION

    def show(self, event=None):
        _ = event
        if not self._view:
            self._view = self._create_view()
            self.application.frame.notebook.AddPage(self._view, "Release Notes", select=False)
        self.application.frame.notebook.show_tab(self._view)

    def show_changelog(self, event=None):
        _ = event
        if not self._dialog:
            self._dialog = HtmlDialog('Offline Change Log', f"Check the online version at https://github.com/"
                                                            f"robotframework/RIDE/blob/{VERSION}/CHANGELOG.adoc")
        self._dialog.SetSize(800, 800)
        # DEBUG: If we LoadFile, we cannot change the foreground color
        # self._dialog.html_wnd.LoadFile(join(dirname(abspath(__file__)), "CHANGELOG.html"))
        with open(join(dirname(abspath(__file__)), "CHANGELOG.html"), 'r', encoding='utf-8') as change_log:
            content = change_log.read()
        fgcolor = self.general_settings[HTML_FOREGROUND]
        if isinstance(fgcolor, tuple):
            fgcolor = '#' + ''.join(hex(item)[2:] for item in fgcolor)
        new_content = content.replace("<body>", f'<body><div><font color="{fgcolor}">') \
            .replace("</body>", "</font></div></body>")
        self._dialog.html_wnd.SetPage(new_content)
        self._dialog.html_wnd.SetBackgroundColour(self.general_settings['background help'])
        self._dialog.html_wnd.SetForegroundColour(fgcolor)
        self._dialog.Show()

    def bring_to_front(self):
        if self._view:
            self.application.frame.notebook.show_tab(self._view)

    def _create_view(self):
        panel = wx.Panel(self.application.frame.notebook)
        html_win = PyClickableHtmlWindow(panel, -1)
        html_win.SetStandardFonts()
        fgcolor = self.general_settings.get(HTML_FOREGROUND, Colour(7, 0, 70))
        panel.SetForegroundColour(fgcolor)
        html_win.SetOwnForegroundColour(fgcolor)
        self.set_content(html_win, WELCOME_TEXT + RELEASE_NOTES)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(html_win, 1, wx.EXPAND | wx.ALL, border=8)
        panel.SetSizer(sizer)
        return panel

    def set_content(self, html_win, content):
        bkgcolor = self.general_settings.get('background help', Colour(240, 242, 80))
        fgcolor = self.general_settings.get(HTML_FOREGROUND, Colour(7, 0, 70))
        if isinstance(bkgcolor, tuple):
            bkgcolor = '#' + ''.join(hex(item)[2:] for item in bkgcolor)
        if isinstance(fgcolor, tuple):
            fgcolor = '#' + ''.join(hex(item)[2:] for item in fgcolor)
        _content = f'<body bgcolor="{bkgcolor}"><div><font color="{fgcolor}">' + content + "</font></div></body>"
        html_win.SetPage(_content)


date = time.strftime('%d/%m/%Y', time.localtime(os.path.getmtime(__file__)))
version = VERSION
milestone = re.split('[ab-]', VERSION)[0]

WELCOME_TEXT = f"""
<h2>Welcome to use RIDE version {version}</h2>

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
"""

# *** DO NOT EDIT THE CODE BELOW MANUALLY ***
# Release notes are updated automatically by package.py script whenever
# a numbered distribution is created.
RELEASE_NOTES = f"""

<div class="document">


<p><a class="reference external" href="https://github.com/robotframework/RIDE/">RIDE (Robot Framework IDE)</a>
 {VERSION} is a new release with minor enhancements and bug fixes. The reference for valid arguments is
 <a class="reference external" href="http://robotframework.org">Robot Framework</a> installed version, which is at this
  moment 6.0.2. However, internal library is based on version 3.1.2, to keep compatibility with old formats.</p>
<p></p>
<ul class="simple">
<li>This version supports Python 3.6 up to 3.10.</li>
<li>There are some changes, or known issues:<ul>
<li>Newlines in Grid Editor are not visible when in navigation mode, but visible in edit mode.</li>
<li>Auto suggestions in Grid Editor can be enabled to not use shortcut to show list.</li>
<li>On Text Editor when Saving the selection of tests in Test Suites (Tree) is cleared.</li>
<li>Test Suite with <em>*** Comments ***</em> can be edited but newlines are introduced.</li>
<li>Some argument types detection (and colorization) is not correct in Grid Editor.</li>
<li>RIDE <strong>DOES NOT KEEP</strong> Test Suites formatting or structure, causing differences in files when used
 on other IDE or Editors.</li>
</ul>
</li>
</ul>
<p><strong>New Features and Fixes Highlights</strong></p>
<ul class="simple">
<li>Added <b>FOR</b> scope markers (<b>IN</b>, <b>IN RANGE</b>, <b>IN ENUMERATE</b>, <b>IN ZIP</b>)
 to auto-complete list</li>
<li>Added support to read environment variable <b>ROBOT_VERSION</b> to apply some conditions</li>
<li>Added notes on Test Timeout Grid Editor field and in Preferences of Test Runner</li>
<li>Keywords auto-suggestion in grid editor does not need shortcut anymore, if you want to enable or disable this
 feature you can config in `Preferences -> Grid Editor -> Enable auto suggestions`</li>

<li>Made \\n visible when editing cells in Grid Editor (problematic in Windows)</li>
<li>Changed alias marker on library imports to consider variable <b>ROBOT_VERSION</b>.
 If version is lower than 6.0, uses <b>WITH NAME</b>, otherwise will use <b>AS</b></li>

<li>Fixed auto-indent on block commands in Text Editor</li>

<li>Fixed missing auto-enclosing when in Cell Editor in Linux</li>

<li>Fixed RIDE will crash when using third party input method in Mac OS</li>

<li>Fixed missing color definition for keyword call in Text Editor</li>

<li>Fixed clearing or emptying fixtures (Setups, Teardowns), now removes headers and synchronizes Text Editor</li>

<li>Fixed selection and persistance of colors in File Explorer and Project Tree panels</li>

<li>Fixed not using defined color for help and HTML content</li>

<li>Fixed missing newlines in sections separation</li>
</ul>
<p>We hope to implement or complete features and make fixes on next major version 2.1 (in the end of 2023).</p>
<p><strong>The minimal wxPython version is, 4.0.7, and RIDE supports the current version, 4.2.0.</strong></p>
<p><em>Linux users are advised to install first wxPython from .whl package at</em> <a class="reference external"
 href="https://extras.wxpython.org/wxPython4/extras/linux/gtk3/">wxPython.org</a>, or by using the system package
  manager.</p>
<p>The <a class="reference external" href="https://github.com/robotframework/RIDE/blob/master/CHANGELOG.adoc">
CHANGELOG.adoc</a> lists the changes done on the different versions.</p>
<p>All issues targeted for RIDE v2.1 can be found
from the <a class="reference external" href="https://github.com/robotframework/RIDE/issues?q=milestone%3Av2.1">issue
 tracker milestone</a>.</p>
<p>Questions and comments related to the release can be sent to the
<a class="reference external" href="http://groups.google.com/group/robotframework-users">robotframework-users</a>
 mailing list or to the channel #ride on
<a class="reference external" href="https://robotframework-slack-invite.herokuapp.com">Robot Framework Slack</a>,
 and possible bugs submitted to the <a class="reference external" href="https://github.com/robotframework/RIDE/issues">
 issue tracker</a>.
You should see <a class="reference external" href="https://forum.robotframework.org/c/tools/ride/">Robot Framework
 Forum</a> if your problem is already known.</p>
<p>To install with <a class="reference external" href="http://pip-installer.org">pip</a> installed, just run</p>
<pre class="literal-block">
pip install --upgrade robotframework-ride=={VERSION}
</pre>
<p>to install exactly this release, which is the same as using</p>
<pre class="literal-block">
pip install --upgrade robotframework-ride
</pre>

<p>Alternatively you can download the source
distribution from <a class="reference external" href="https://pypi.python.org/pypi/robotframework-ride">PyPI</a> and
 install it manually. For more details and other
installation approaches, see the <a class="reference external"
 href="https://github.com/robotframework/RIDE/wiki/Installation-Instructions">installation instructions</a>.
If you want to help in the development of RIDE, by reporting issues in current development version, you can install
 with:</p>
<pre class="literal-block">
pip install -U https://github.com/robotframework/RIDE/archive/master.zip
</pre>
<p>Important document for helping with development is the <a class="reference external"
 href="https://github.com/robotframework/RIDE/blob/master/CONTRIBUTING.adoc">CONTRIBUTING.adoc</a>.</p>
<p>See the <a class="reference external" href="https://github.com/robotframework/RIDE/wiki/F.A.Q.">FAQ</a> for
 important info about <cite>: FOR</cite> changes and other known issues and workarounds.</p>
<p>A possible way to start RIDE is:</p>
<pre class="literal-block">
python -m robotide.__init__
</pre>
<p>You can then go to <cite>Tools&gt;Create RIDE Desktop Shortcut</cite>, or run the shortcut creation script with:</p>
<pre class="literal-block">
python -m robotide.postinstall -install
</pre>
<p>RIDE {VERSION} was released on 08/May/2023.</p>
</div>
"""
