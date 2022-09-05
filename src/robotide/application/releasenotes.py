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

import wx
from wx import Colour
from wx.lib.ClickableHtmlWindow import PyClickableHtmlWindow
from os.path import abspath, join, dirname

from ..action import ActionInfo
from ..version import VERSION
from ..widgets import HtmlDialog
# from ..widgets.htmlwnd import HTML_BACKGROUND


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
        if not self._view:
            self._view = self._create_view()
            self.application.frame.notebook.AddPage(self._view, "Release Notes", select=False)
        self.application.frame.notebook.show_tab(self._view)

    def show_changelog(self, event=None):
        if not self._dialog:
            self._dialog = HtmlDialog('Offline Change Log', 'Check the online version at https://github.com/robotframework/RIDE/blob/master/CHANGELOG.adoc')
        self._dialog.SetSize(800, 800)
        self._dialog.html_wnd.LoadFile(join(dirname(abspath(__file__)), "CHANGELOG.html"))
        self._dialog.html_wnd.SetBackgroundColour(self.general_settings['background help'])
        self._dialog.html_wnd.SetForegroundColour(self.general_settings['foreground text'])
        self._dialog.Show()

    def bring_to_front(self):
        if self._view:
            self.application.frame.notebook.show_tab(self._view)

    def _create_view(self):
        panel = wx.Panel(self.application.frame.notebook)
        html_win = PyClickableHtmlWindow(panel, -1)
        html_win.SetStandardFonts()
        fgcolor = self.general_settings.get('foreground text', Colour(7, 0, 70))
        """
        panel.SetBackgroundColour(Colour(200, 222, 40))
        """
        panel.SetForegroundColour(fgcolor)
        html_win.SetOwnForegroundColour(fgcolor)
        self.set_content(html_win, WELCOME_TEXT + RELEASE_NOTES)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(html_win, 1, wx.EXPAND|wx.ALL, border=8)
        panel.SetSizer(sizer)
        return panel

    def set_content(self, html_win, content):
        bkgcolor = self.general_settings.get('background help', Colour(240, 242, 80))
        fgcolor = self.general_settings.get('foreground text', Colour(7, 0, 70))
        # print(f"DEBUG: set_content  bkg={bkgcolor} bkg={type(bkgcolor)} fg={fgcolor} fg={type(fgcolor)}")
        try:
            # tuple(bkgcolor)
            bcolor = ''.join(hex(item)[2:] for item in bkgcolor)
            fcolor = ''.join(hex(item)[2:] for item in fgcolor)
            _content = '<body "bgcolor=#%s;" "color=#%s;">%s</body>' % (bcolor, fcolor, content)
            # print(f"DEBUG: set_content after  bkg={bcolor} bkg={type(bcolor)} fg={fcolor} fg={type(fcolor)}")
        except TypeError:
            _content = '<body bgcolor=%s>%s</body>' % (bkgcolor, content)
        html_win.SetPage(_content)


import time, os, re

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


<p><a class="reference external" href="https://github.com/robotframework/RIDE/">RIDE (Robot Framework IDE)</a> v2.0b2 is a new release with major enhancements and bug fixes.
This version v2.0b2 includes removal of Python 2.7 support. The reference for valid arguments is <a class="reference external" href="http://robotframework.org">Robot Framework</a> installed version, which is at this moment 5.0.1. However, internal library is based on version 3.1.2, to keep compatibility with old formats.</p>
<ul class="simple">
<li>This is the <strong>first version without support for Python 2.7</strong>.</li>
<li>The last version with support for Python 2.7 was <strong>1.7.4.2</strong>.</li>
<li>Support for Python 3.6 up to 3.10 (current version on this date).</li>
<li>There are some important changes, or known issues:
<ul>
<li>On MacOS to call autocomplete in Grid and Text Editors, you have to use Alt-Space (not Command-Space).</li>
<li>On Linux and Windows to call autocomplete in Grid and Text Editors, you have to use Ctrl-Space.</li>
<li>On Text Editor the TAB key adds the defined number of spaces. With Shift moves to the left, and together with Control selects text.</li>
<li>On Text Editor the <strong>: FOR</strong> loop structure must use Robot Framework 3.1.2 syntax, i.e. <strong>FOR</strong> and <strong>END</strong>.</li>
<li>On Grid Editor and Linux the auto enclose is only working on cell selection, but not on cell content edit.</li>
<li>On Text Editor when Saving the selection os tests in Test Suites (Tree) is cleared.</li>
</ul>
</li>
</ul>
<p><strong>New Features and Fixes Highlights</strong></p>
<ul class="simple">
<li>Auto enclose text in &#123;&#125;, [], &quot;&quot;, ''</li>
<li>Auto indent in Text Editor on new lines</li>
<li>Block indent in Text Editor (TAB on block of selected text)</li>
<li>Ctrl-number with number, 1-5 also working on Text Editor:<ol class="arabic">
<li>create scalar variable</li>
<li>create list variable</li>
<li>Comment line</li>
<li>Uncomment line</li>
<li>create dictionary variable</li>
</ol>
</li>
<li>Persistence of the position and state of detached panels, File Explorer and Test Suites</li>
<li>File Explorer and Test Suites panels are now Plugins and can be disabled or enabled and made Visible with F11 and F12</li>
<li>File Explorer now shows selected file when RIDE starts</li>
<li>Block comment and uncomment on both Grid and Text editors</li>
<li>Extensive color customization of panel elements via <cite>Tools&gt;Preferences</cite></li>
<li>Color use on Console and Messages Log panels on Test Run tab</li>
</ul>
<p>Please note, that the features and fixes are not yet closed. This pre-release is being done because it has important fixes.</p>
<p><strong>The minimal wxPython version is, 4.0.7, and RIDE supports the current version, 4.2.0.</strong></p>
<p><em>Linux users are advised to install first wxPython from .whl package at</em> <a class="reference external" href="https://extras.wxpython.org/wxPython4/extras/linux/gtk3/">wxPython.org</a>.</p>
<p>The <a class="reference external" href="https://github.com/robotframework/RIDE/blob/master/CHANGELOG.adoc">CHANGELOG.adoc</a> lists the changes done on the different versions.</p>
<p>All issues targeted for RIDE v2.0 can be found
from the <a class="reference external" href="https://github.com/robotframework/RIDE/issues?q=milestone%3Av2.0">issue tracker milestone</a>.</p>
<p>Questions and comments related to the release can be sent to the
<a class="reference external" href="http://groups.google.com/group/robotframework-users">robotframework-users</a> mailing list or to the channel #ride on
<a class="reference external" href="https://robotframework-slack-invite.herokuapp.com">Robot Framework Slack</a>, and possible bugs submitted to the <a class="reference external" href="https://github.com/robotframework/RIDE/issues">issue tracker</a>.
You should see <a class="reference external" href="https://forum.robotframework.org/c/tools/ride/">Robot Framework Forum</a> if your problem is already known.</p>
<p>If you have <a class="reference external" href="http://pip-installer.org">pip</a> installed, just run</p>
<pre class="literal-block">
pip install --pre --upgrade robotframework-ride==2.0b2
</pre>
<p>to install this <strong>BETA</strong> release, and for the <strong>final</strong> release use</p>
<pre class="literal-block">
pip install --upgrade robotframework-ride
</pre>
<pre class="literal-block">
pip install robotframework-ride==2.0
</pre>
<p>to install exactly the <strong>final</strong> version. Alternatively you can download the source
distribution from <a class="reference external" href="https://pypi.python.org/pypi/robotframework-ride">PyPI</a> and install it manually. For more details and other
installation approaches, see the <a class="reference external" href="https://github.com/robotframework/RIDE/wiki/Installation-Instructions">installation instructions</a>.
If you want to help in the development of RIDE, by reporting issues in current development version, you can install with:</p>
<pre class="literal-block">
pip install -U https://github.com/robotframework/RIDE/archive/master.zip
</pre>
<p>See the <a class="reference external" href="https://github.com/robotframework/RIDE/wiki/F.A.Q.">FAQ</a> for important info about <cite>: FOR</cite> changes and other known issues and workarounds.</p>
<p>A possible way to start RIDE is:</p>
<pre class="literal-block">
python -m robotide.__init__
</pre>
<p>You can then go to <cite>Tools&gt;Create RIDE Desktop Shortcut</cite>, or run the shortcut creation script with:</p>
<pre class="literal-block">
python -m robotide.postinstall -install
</pre>
<p>RIDE v2.0b2 was released on 05/Sep/2022.</p>
</div>
"""
