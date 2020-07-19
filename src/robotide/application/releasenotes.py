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
        self.application.frame.actions.register_action(ActionInfo('Help', 'Release Notes',
                                                                  self.show,
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


<p><a class="reference external" href="https://github.com/robotframework/RIDE/">RIDE (Robot Framework IDE)</a> {version} is a new release with major enhancements
and bug fixes. This version {version} includes removal of Python 2.7 support.
The reference for valid arguments is <a class="reference external" href="http://robotframework.org">Robot Framework</a> version 3.1.2.
<!-- <strong>MORE intro stuff...</strong>-->
</p>
<ul class="simple">
<li>This is the <strong>first version without support for Python 2.7</strong>.</li>
<li>The last version with support for Python 2.7 was <strong>1.7.4.2</strong>.</li>
<li>There are some important changes, or known issues:<ul>
<li>On MacOS to call autocomplete in Grid and Text Editors, you have to use Alt-Space (not Command-Space).</li>
<li>On Linux and Windows to call autocomplete in Grid and Text Editors, you have to use Ctrl-Space.</li>
<li>On Text Editor the TAB key adds the defined number of spaces. With Shift moves to the left, and together with Control selects text.</li>
<li>On Text Editor the <strong>: FOR</strong> loop structure must use Robot Framework 3.1.2 syntax, i.e. <strong>FOR</strong> and <strong>END</strong>. The only solution to disable this, is to disable Text Editor Plugin.</li>
<li>On Grid Editor and Linux the auto enclose is only working on cell selection, but not on cell content edit.</li>
<li>On Text Editor when Saving with Ctrl-S, you must do this twice :(.</li>
</ul>
</li>
</ul>
<p><strong>New Features and Fixes Highlights</strong></p>
<ul>
<li>Auto enclose text in {{}}, [], "", ''</li>
<li>Auto indent in Text Editor</li>
<li>Block indent in Text Editor (TAB on block of selected text)</li>
<li>Ctrl-number with number, 1-5 also working on Text Editor:<ol><li>create scalar variable</li><li>create list variable</li>
<li>Comment line</li><li>Uncomment line</li><li>create dictionary variable</li></ol></li>
<li>Persistence of the position and state of detached panels, File Explorer and Test Suites</li>
<li>File Explorer and Test Suites panels are now Plugins and can be disabled or enabled and made Visible with F11 and F12</li>
<li>File Explorer now shows selected file when RIDE starts</li>
</ul>
<p>Please note, that the features and fixes are not yet closed. This pre-release is being done because it has important fixes.
</p>
<p><strong>wxPython will be updated to version 4.0.7post2</strong></p>
<p><strong>wxPython version 4.1, is not recommended to be used with RIDE.</strong></p>
<p><em>Linux users are advised to install first wxPython from .whl package at</em> <a class="reference external" href="https://extras.wxpython.org/wxPython4/extras/linux/gtk3/">wxPython.org</a>.</p>
<!-- <p><strong>REMOVE reference to tracker if release notes contain all issues.</strong></p>-->

<p>All issues targeted for RIDE {milestone} can be found
from the <a class="reference external" href="https://github.com/robotframework/RIDE/issues?q=milestone%3A{milestone}">issue tracker milestone</a>.</p>
<p>Questions and comments related to the release can be sent to the
<a class="reference external" href="http://groups.google.com/group/robotframework-users">robotframework-users</a> mailing list, to the <a class="reference external" href="https://forum.robotframework.org/c/tools/ride/21">RIDE topic on Robot Framework Forum</a> or to the channel #ride on
<a class="reference external" href="https://robotframework-slack-invite.herokuapp.com">Robot Framework Slack</a>, and possible bugs submitted to the <a class="reference external" href="https://github.com/robotframework/RIDE/issues">issue tracker</a>.</p>
<!-- <p><strong>REMOVE ``--pre`` from the next command with final releases.</strong> -->
If you have <a class="reference external" href="http://pip-installer.org">pip</a> installed, just run</p>
<pre class="literal-block">
pip install --pre --upgrade robotframework-ride==2.0b1
</pre>
<p>to install this <strong>BETA</strong> release, and for the <strong>final</strong> release use</p>
<pre class="literal-block">
pip install --upgrade robotframework-ride
</pre>
<pre class="literal-block">
pip install robotframework-ride=={version}
</pre>
<p>to install exactly the <strong>final</strong> version. Alternatively you can download the source
distribution from <a class="reference external" href="https://pypi.python.org/pypi/robotframework-ride">PyPI</a> and install it manually. For more details and other
installation approaches, see the <a class="reference external" href="https://github.com/robotframework/RIDE/wiki/Installation-Instructions">installation instructions</a>.
See the <a class="reference external" href="https://github.com/robotframework/RIDE/wiki/F.A.Q.">FAQ</a> for important info about <cite>: FOR</cite> changes.</p>
<p>A possible way to start RIDE is:</p>
<pre class="literal-block">
python -m robotide.__init__
</pre>
<p>You can then go to <cite>Tools&gt;Create RIDE Desktop Shortcut</cite>, or run the shortcut creation script with:</p>
<pre class="literal-block">
python -m robotide.postinstall -install
</pre>
<p>RIDE {version} was released on {date}.</p>
</div>

<h2>Release notes for v2.0b1</h2>
<table border="1">
<tr>
<td><p><b>ID</b></p></td>
<td><p><b>Type</b></p></td>
<td><p><b>Priority</b></p></td>
<td><p><b>Summary</b></p></td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2237">Issue 2237</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Fix win10 system freeze when loading large project</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2236">Issue 2236</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Fix cannot edit grid cell with wxPython 4.1.0</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2234">Issue 2234</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Added Changelog</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2232">Issue 2232</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Redesign RideEventHandler and file system monitoring feature</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2230">Issue 2230</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Fix delete save txt</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2229">Issue 2229</a></td>
<td>bug</td>
<td>high</td>
<td>Cannot delete and save text in text editor</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2223">Issue 2223</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Fixed issue#2108:</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2221">Issue 2221</a></td>
<td>enhancement</td>
<td>high</td>
<td>Fix dynamic doc</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2220">Issue 2220</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Bug fixing on perference panel</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2219">Issue 2219</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Fixes tree selection, because of wrong variable name.</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2217">Issue 2217</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Nyral/fix encodings</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2216">Issue 2216</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Bugs fixing on editor grid</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2215">Issue 2215</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Fixes error message on RIDE Log about missing clear_all.</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2214">Issue 2214</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Fix tree node</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2212">Issue 2212</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Fix parsing warning of report/ log html file</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2210">Issue 2210</a></td>
<td>enhancement</td>
<td>high</td>
<td>Fix for 1668: Given a large test suite, selecting all tests from the root of tree, freezes RIDE for some time</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2205">Issue 2205</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Update treenodehandlers.py to prevent freeze ups</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2199">Issue 2199</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Better error and removal of old log files.</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2198">Issue 2198</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Log misc fixes</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2197">Issue 2197</a></td>
<td>bug</td>
<td>low</td>
<td>Taking log plugin into use failed</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2195">Issue 2195</a></td>
<td>bug</td>
<td>high</td>
<td>Keywords not highlighted and no suggestion for them in RIDE</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2189">Issue 2189</a></td>
<td>bug</td>
<td>high</td>
<td>Problems with input in Grid Editor after wxPython 4.1 upgrade.</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2186">Issue 2186</a></td>
<td>bug</td>
<td>Unknown priority</td>
<td>Unable to Create new project on 2.0b1.dev1</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2184">Issue 2184</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Adds conditions for wxPython 4.1.0</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2181">Issue 2181</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Indents and de-indents block of selected text</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2180">Issue 2180</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Adds ! to Save item on menu. Not detected when removed.</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2179">Issue 2179</a></td>
<td>task</td>
<td>critical</td>
<td>Bring back Save option!!!!!</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2178">Issue 2178</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Fix keys</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2177">Issue 2177</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Implement auto tab</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2176">Issue 2176</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Implement auto indent in Text Editor:</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2175">Issue 2175</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Fixes {{ and [ in grid editor. Still disable in cell editor, on Linux</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2174">Issue 2174</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Fixes selection in keywords list suggestion</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2173">Issue 2173</a></td>
<td>bug</td>
<td>low</td>
<td>Keywords help list, pressing down arrow, makes beep and does not move selection</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2170">Issue 2170</a></td>
<td>bug</td>
<td>low</td>
<td>When the name of the test case contains Chinese, the output log shows garbled code. How to fix this？</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2167">Issue 2167</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Fix keys in Grid Editor, [ and {{ still don't trigger</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2166">Issue 2166</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Keep a CHANGELOG.adoc file</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2165">Issue 2165</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Fix keys</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2163">Issue 2163</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Text Editor - Encloses text in Cell or selected text with certain</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2158">Issue 2158</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Encloses text in Cell or selected text with certain symbols</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2157">Issue 2157</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Fixes default arguments keyword help, #2134</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2154">Issue 2154</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Added white color to inside the icon face</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2152">Issue 2152</a></td>
<td>enhancement</td>
<td>high</td>
<td>Turns Test Suite Tree and File Explorer into Plugins</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2148">Issue 2148</a></td>
<td>enhancement</td>
<td>medium</td>
<td>RIDE TaskBar icon in Win10 is black on dark grey... hard to see</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2146">Issue 2146</a></td>
<td>bug</td>
<td>high</td>
<td>RIDE crashes when you delete a tag via the GUI</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2145">Issue 2145</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td> ride 1.7.4.1 CTRL + 1 function is available, but the content is not in ${{}}, now ${{}} is outside</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2144">Issue 2144</a></td>
<td>bug</td>
<td>low</td>
<td>Pressing F2 in Grid Editor on MacOS starts editor on Project Tree item not on Cell</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2143">Issue 2143</a></td>
<td>enhancement</td>
<td>high</td>
<td>Make Project Tree and File Explorer panels, Plugins.</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2142">Issue 2142</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Cleans up unittests</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2141">Issue 2141</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Fixes reprocessing of %date% %time% variables on Windows</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2140">Issue 2140</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Fixed focus issue when using F2 to edit grid cell</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2138">Issue 2138</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Fix travis</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2137">Issue 2137</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Fixes unit tests for #2128</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2135">Issue 2135</a></td>
<td>bug</td>
<td>medium</td>
<td>Cannot edit existing cell text with F2</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2134">Issue 2134</a></td>
<td>bug</td>
<td>Unknown priority</td>
<td>Ride does not display the correct default values for library keywords in usage</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2130">Issue 2130</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Adds an autoclose timer to the Create Shortcut dialog.</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2128">Issue 2128</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Fixed Python 3.8 incompatibility</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2125">Issue 2125</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>wx.NewId() to wx.NewIdRef()</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2124">Issue 2124</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Removes Python 2.7 support</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2122">Issue 2122</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>How to force silent or unattend installation via pip?</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2121">Issue 2121</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Cleanup of wxPython/wxPhoenix version conditioning</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2108">Issue 2108</a></td>
<td>bug</td>
<td>medium</td>
<td>Resource files with extension .resource are not shown in Tree if not used</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2098">Issue 2098</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Ride.py is not opening the IDE</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2086">Issue 2086</a></td>
<td>enhancement</td>
<td>Unknown priority</td>
<td>Separates AppendText for MessagesLog. Adds process memory limit on Me…</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2060">Issue 2060</a></td>
<td>bug</td>
<td>Unknown priority</td>
<td>RIDE GUI App failing to start due to setlocale() error</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2039">Issue 2039</a></td>
<td>bug</td>
<td>Unknown priority</td>
<td>Can not see grid in Edit Settings - test case</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/2029">Issue 2029</a></td>
<td>bug</td>
<td>high</td>
<td>RIDE 1.7.4b2 arguments are ignored</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1983">Issue 1983</a></td>
<td>bug</td>
<td>low</td>
<td>Fix Runner Log window Chinese and Latin encoding chars on Windows</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1975">Issue 1975</a></td>
<td>none</td>
<td>Unknown priority</td>
<td>Ride EDIT screen is blank</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1944">Issue 1944</a></td>
<td>enhancement</td>
<td>low</td>
<td>"Make scalar/list variable body" shortcuts(ctrl+1, ctrl+2) cursor position</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1930">Issue 1930</a></td>
<td>bug</td>
<td>medium</td>
<td>Editors need refresh when files modified outside of RIDE by external editors</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1843">Issue 1843</a></td>
<td>enhancement</td>
<td>high</td>
<td>System freezes on Windows 10</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1576">Issue 1576</a></td>
<td>bug</td>
<td>Unknown priority</td>
<td>Manage Plugins not working 1.5.1 (wxPython3)</td>
</tr>
<tr>
<td><a href="http://github.com/robotframework/RIDE/issues/1554">Issue 1554</a></td>
<td>enhancement</td>
<td>critical</td>
<td>Support wxPython3</td>
</tr>
</table>
<p>Altogether 73 issues.</p>
"""
