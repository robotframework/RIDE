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

import builtins
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

_ = wx.GetTranslation  # To keep linter/code analyser happy
builtins.__dict__['_'] = wx.GetTranslation

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
        self.application.frame.actions.register_action(ActionInfo(_('Help'), _('Release Notes'),
                                                                  self.show,
                                                                  doc=_('Show the release notes')))
        self.application.frame.actions.register_action(ActionInfo(_('Help'), _('Offline Change Log'),
                                                                  self.show_changelog,
                                                                  doc=_('Show the offline CHANGELOG')))
        self.show_if_updated()

    def show_if_updated(self):
        if self.version_shown != VERSION:
            self.show()
            self.application.settings['version_shown'] = VERSION

    def show(self, event=None):
        __ = event
        if not self._view:
            self._view = self._create_view()
            self.application.frame.notebook.AddPage(self._view, _("Release Notes"), select=False)
        self.application.frame.notebook.show_tab(self._view)

    def show_changelog(self, event=None):
        __ = event
        if not self._dialog:
            self._dialog = HtmlDialog(_('Offline Change Log'),
                                      _("Check the online version at ") +
                                      f"https://github.com/robotframework/RIDE/blob/{VERSION}/CHANGELOG.adoc")
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

<h2 align='center'>RIDE is celebrating 16 years on this date!</h2>

<p><a class="reference external" href="https://github.com/robotframework/RIDE/">RIDE (Robot Framework IDE)</a>
 {VERSION} is a new release with important enhancements and bug fixes. The reference for valid arguments is
 <a class="reference external" href="https://robotframework.org/">Robot Framework</a> installed version, which is at
  this
  moment 7.1. However, internal library code is originally based on version 3.1.2, but adapted for new versions.</p>
<p></p>
<ul class="simple">
<li>This version supports Python 3.8 up to 3.12.</li>
<li>There are some changes, or known issues:<ul>
<li>❌ - Removed support for Python 3.6 and 3.7</li>
<li>✔ - Fixed recognition of variables imported from YAML, JSON and Python files.</li>
<li>✔ - Added a setting for a specific Browser by editing the settings.cfg file. Add the string parameter 
<b>browser</b> in the section <b>[Plugins][[Test Runner]]</b></li>
<li>✔ - Fixed on Text Editor when Saving the selection of tests to run in Test Suites (Tree) is cleared.</li>
<li>✔ - Added Korean language support for UI.</li>
<li>✔ - Added <b>caret style</b> to change insert caret to 'block' or 'line' in Text Editor, by editing 
<em>settings.cfg</em>. The color of the caret is the same as 'setting' and will be adjusted for better contrast with the
 background.</li>
<li>✔ - Allow to do auto-suggestions of keywords in Text Editor without a shortcut, if you want to enable or disable 
this feature you can config in `Tools -> Preferences -> Text Editor -> Enable auto suggestions`.</li>
<li>✔ - Added support for Setup in keywords, since Robot Framework version 7.0.</li>
<li>✔ - Added support for new VAR marker, since Robot Framework version 7.0.</li>
<li>✔ - Added to Grid Editor changing Zoom In/Out with <b>Ctrl-Mouse Wheel</b> and setting at Preferences.</li>
<li>✔ - Fixed plugin Run Anything (Macros) not showing output and broken actions.</li>
<li>✔ - Added actions on columns of Grid Editor: Double-Click or Right Mouse Click, allows to edit the column name for
 Data 
Driven or Templated; Left Mouse Click, selects the column cells.</li>
<li>✔ - Added command line option, <b>--settingspath</b>, to select a different configuration.</li>
<li>✔ - Added different settings file, according the actual Python executable, if not the original installed.</li>
<li>✔ - Added a selector for Tasks and Language to the New Project dialog.</li>
<li>✔ - Added UI localization prepared for all the languages from installed Robot Framework version 6.1, or 
higher. Major translations are: Dutch, Portuguese and Brazilian Portuguese. Still missing translation 
of some elements.</li> 
<li>✔ - Added support for language configured test suites, with languages from installed Robot Framework version 6.1,
 or 
higher.</li> 
<li>✔ - On Text Editor, pressing <b>Ctrl</b> when the caret/cursor is near a Keyword will show a detachable window with
 the 
documentation, at Mouse Pointer position.</li> 
<li>✔ - RIDE tray icon now shows a context menu with options Show, Hide and Close.</li>
<li>✔ - Highlighting and navigation of selected Project Explorer items, in Text Editor.</li>
<li>✔ - When editing in Grid Editor with content assistance, the selected content can be edited by escaping the list of 
suggestions with keys ARROW_LEFT or ARROW_RIGHT.</li>
<li>✔ - Newlines in Grid Editor can be made visible with the <b>filter newlines</b> set to False.</li>
<li>🐞 - Problems with COPY/PASTE in Text Editor have been reported when using wxPython 4.2.0, but not with 
version 4.2.1 and 4.2.2, which we now <em>recommend</em>.</li>
<li>🐞 - Some argument types detection (and colorization) is not correct in Grid Editor.</li>
<li>🐞 - RIDE <strong>DOES NOT KEEP</strong> Test Suites formatting or structure, causing differences in files when used
 on other IDE or Editors.</li>
</ul>
</li>
</ul>
<p><strong>New Features and Fixes Highlights</strong></p>
<ul class="simple">
<li>Fixed recognition of variables imported from YAML, JSON and Python files.</li>
<li>Added a setting for a specific Browser by editing the settings.cfg file. Add the string parameter 
<b>browser</b> in the section <b>[Plugins][[Test Runner]]</b></li>
<li>Changed the order of insert and delete rows in Grid Editor rows context menu.</li>
<li>Fixed validation of multiple arguments with default values in Grid Editor.</li>
<li>Added color to Test Runner Console Log final output, report and log since RF v7.1rc1.</li>
<li>Fixed on Text Editor when Saving the selection of tests to run in Test Suites (Tree) is cleared.</li>
<li>Added Korean language support for UI, experimental.</li>
<li>Fixed wrong item selection, like Test Suite, when doing right-click actions in Project Explorer.</li>
<li>Fixed delete variable from Test Suite settings remaining in Project Explorer.</li>
<li>Added <b>caret style</b> to change insert caret to 'block' or 'line' in Text Editor, by editing 
<em>settings.cfg</em>. The color of the caret is the same as 'setting' and will be adjusted for better contrast with the
 background.</li>
<li>Fixed obsfuscation of Libraries and Metadata panels when expanding Settings in Grid Editor and Linux systems.</li>
<li>Allow to do auto-suggestions of keywords in Text Editor without a shortcut, if you want to enable or disable 
this feature you can config in `Tools -> Preferences -> Text Editor -> Enable auto suggestions`.</li>
<li>Added support for Setup in keywords, since Robot Framework version 7.0.</li>
<li>Fixed multiline variables in Variables section. In Text Editor they are separated by ... continuation marker.
In Grid Editor use | (pipe) to separate lines.</li>
<li>Added support for new VAR marker, since Robot Framework version 7.0.</li>
<li>Added configurable style of the tabs in notebook pages, Edit, Text, Run, etc. Parameter <b>notebook theme</b> 
 takes values from 0 to 5. See wxPython, demo for agw.aui for details.</li>
<li>Added UI localization and support for Japanese configured test suites, valid for Robot Framework version 7.0.1 or
 higher.</li>
<li>Fixed keywords Find Usages in Grid Editor not finding certain values when using Gherkin.</li>
<li>Improved selection of items from Tree in Text Editor. Now finds more items and selects whole line.</li>
<li>Changed output in plugin Run Anything (Macros) to allow Zoom In/Out, and Copy content.</li>
<li>Added to Grid Editor changing Zoom In/Out with <b>Ctrl-Mouse Wheel</b> and setting at Preferences.</li>
<li>Fixed plugin Run Anything (Macros) not showing output and broken actions.</li>
<li>Added actions on columns of Grid Editor: Double-Click or Right Mouse Click, allows to edit the column name for Data 
Driven or Templated; Left Mouse Click, selects the column cells.</li>
<li>Added command line option, <b>--settingspath</b>, to select a different configuration.</li>
<li>Added different settings file, according the actual Python executable, if not the original installed.</li>
<li>Fixed headers and blank spacing in Templated tests.</li>
<li>Added context option <b>Open Containing Folder</b> to test suites directories in Project Explorer.</li>
<li>Added a setting for a specific file manager by editing the settings.cfg file. Add the string parameter 
<b>file manager</b>
in the section <b>[General]</b></li>
<li>Added minimal support to have comment lines in Import settings. These are not supposed to be edited in Editor, 
and new lines are added at Text Editor.</li>
<li>Fixed removal of continuation marker in steps</li>
<li>Fixed wrong continuation of long chains of keywords in Setups, Teardowns or Documentation.</li>
<li>Added a selector for Tasks and Language to the New Project dialog. Still some problems: Tasks type changes to Tests,
localized sections only stay translated after Apply in Text Editor.</li>
<li>Added UI localization prepared for all the languages from installed Robot Framework version 6.1, or 
higher. Language is selected from Tools->Preferences->General.</li>
<li>Removed support for HTML file format (obsolete since Robot Framework 3.2)</li>
<li>Added support for language configured test suites. Fields are shown in the language of the files in Grid Editor.
 Tooltips are always shown in English. Colorization for language configured files is working in Text Editor.</li>
<li>Fixed New User Keyword dialog not allowing empty Arguments field</li>
<li>Fixed escaped spaces showing in Text Editor on commented cells</li>
<li>Improved keywords documentation search, by adding current dir to search</li>
<li>Improved Move up/down, <b>Alt-UpArrow</b>/<b>Alt-DownArrow</b> in Text Editor, to have proper indentation and 
selection</li>
<li>Added auto update check when development version is installed</li>
<li>Added menu option <b>Help-&gt;Check for Upgrade</b> which allows to force update check and install development 
version</li>
<li>Added <b>Upgrade Now</b> action to update dialog.</li>
<li>Added <b>Test Tags</b> field (new, since Robot Framework 6.0) to Test Suites settings. This field will replace 
<b>Default</b> and <b>Force Tags</b> settings, after Robot Framework 7.0</li>
<li>Improved <b>RIDE Log</b> and <b>Parser Log</b> windows to allow Zoom In/Out with <b>Ctrl-Mouse Wheel</b></li>
<li>Hide continuation markers in Project Tree</li>
<li>Improved content assistance in Text Editor by allowing to filter list as we type</li>
<li>Fixed resource files disappearing from Project tree on Windows</li>
<li>Fixed missing indication of link for User Keyword, when pressing <b>Ctrl</b> in Grid Editor</li>
<li>Added content help pop-up on Text Editor by pressing <b>Ctrl</b> for text at cursor position or selected 
autocomplete list item</li>
<li>Added Exclude option in context nenu for Test files, previously was only possible for Test Suites folders</li>
<li>Added exclusion of monitoring filesystem changes for files and directories excluded in Preferences</li>
<li>Fixed exception when finding GREY color for excluded files and directories in Project Tree</li>
<li>Added support for JSON variables, by using the installed Robot Framework import method</li>
<li>Colorization of Grid Editor cells after the continuation marker <b>...</b> and correct parsing of those lines</li> 
<li>Colorization of Grid Editor cells when contents is list or dictionary variables</li>
<li>Added indication of matching brackets, <b>()</b>, <b>"""'''{}'''f"""</b>, <b>[]</b>, in Text Editor</li>
<li>Fixed non synchronized expanding/collapse of Settings panel in Grid Editor, on Linux</li>
<li>Fixed not working the deletion of cells commented with <b># </b> in Grid Editor with <b>Ctrl-Shift-D</b></li> 
<li>Fixed empty line being always added to the Variables section in Text Editor</li>
<li>Improved project file system changes and reloading</li>
<li>Added context menu to RIDE tray icon. Options Show, Hide and Close</li>
<li>Added synchronization with Project Explorer to navigate to selected item, Test Case, Keyword, Variable, in Text
 Editor</li>
<li>Control commands (<b>FOR</b>, <b>IF</b>, <b>TRY</b>, etc) will only be colorized as valid keywords when typed in 
all caps in Grid Editor</li>
<li>Newlines in Grid Editor can be made visible with the <b>filter newlines</b> set to False, by editing 
<em>settings.cfg</em></li>
<li>Improve auto-suggestions of keywords in Grid Editor by allowing to close suggestions list with keys ARROW_LEFT or 
ARROW_RIGHT</li>
<li>Improve Text Editor auto-suggestions by using: selected text, text at left or at right of cursor</li>
</ul>
<!-- <p>We hope to implement or complete features and make fixes on next major version 2.1 (in mid Autumm of 2024).</p>
-->
<p><strong>The minimal wxPython version is, 4.0.7, and RIDE supports the current version, 4.2.2, which we recommend.
</strong></p>
<p><em>Linux users are advised to install first wxPython from .whl package at</em> <a class="reference external"
 href="https://extras.wxpython.org/wxPython4/extras/linux/gtk3/">wxPython.org</a>, or by using the system package
  manager.</p>
<p>The <a class="reference external" href="https://github.com/robotframework/RIDE/blob/master/CHANGELOG.adoc">
CHANGELOG.adoc</a> lists the changes done on the different versions.</p>
<p>All issues targeted for RIDE v2.1 can be found
from the <a class="reference external" href="https://github.com/robotframework/RIDE/issues?q=milestone%3Av2.1">issue
 tracker milestone</a>.</p>
<p>Questions and comments related to the release can be sent to the
<a class="reference external" href="https://groups.google.com/group/robotframework-users">robotframework-users</a>
 mailing list or to the channel #ride on
<a class="reference external" href="https://robotframework-slack-invite.herokuapp.com">Robot Framework Slack</a>,
 and possible bugs submitted to the <a class="reference external" href="https://github.com/robotframework/RIDE/issues">
 issue tracker</a>.
You should see <a class="reference external" href="https://forum.robotframework.org/c/tools/ride/">Robot Framework
 Forum</a> if your problem is already known.</p>
<p>To install with <a class="reference external" href="https://pypi.org/project/pip/">pip</a> installed, just run</p>
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
<p>To start RIDE from a command window, shell or terminal, just enter:</p>
<pre>ride</pre>
<p>You can also pass some arguments, like a path for a test suite file or directory.<p>
<pre>ride example.robot</pre>
<p>Another possible way to start RIDE is:</p>
<pre class="literal-block">
python -m robotide.__init__
</pre>
<p>You can then go to <cite>Tools&gt;Create RIDE Desktop Shortcut</cite>, or run the shortcut creation script with:</p>
<pre class="literal-block">python -m robotide.postinstall -install</pre>
<p>or</p>
<pre class="literal-block">ride_postinstall.py -install</pre>
<p>RIDE {VERSION} was released on 13/October/2024 (<a href="https://github.com/robotframework/RIDE/wiki/Old-Release-Notes
#ride-010">16 years after its first version</a>).</p>
<!-- <br/>
<h3>May The Fourth Be With You!</h3>
<h3>Celebrate the bank holiday, 10th June, Day of Portugal, Portuguese Communities and Camões!!</h3>
<h3 align='center'>🇵🇹</h3>
-->
</div>
"""
