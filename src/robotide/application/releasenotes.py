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
<h1>Robot Framework IDE 1.7.4b2</h1>
<p><a href="https://github.com/robotframework/RIDE/">RIDE (Robot Framework IDE)</a> 1.7.4b2 is a new release with major enhancements
and bug fixes. This version 1.7.4b2 includes fixes for installer, Font Type selection, Text Editor improvements and new File explorer.</br>
The reference for valid arguments is <a href="http://robotframework.org" rel="nofollow">Robot Framework</a> version 3.1.2.</p>
<h2>The most notable enhancements (for version 1.7.4) are:</h2>
<ul class="simple">
<li>This is the <strong>last version supporting Python 2.7</strong>.</li>
<li>A new File Explorer allows to open supported file types in RIDE, or other types in a basic code editor. To open a file you must double-click on it (project folders open with right-click). If it is a supported file format but not with the correct structure (for example a resource file), an error message is shown, and then opens in code editor.</li>
<li>On Grid Editor, the cells can be autoajusting with wordwrap. There is a new checkbox in <code>Tools&gt;Preferences&gt;Grid Editor</code>.</li>
<li>Font Type selection is available for Text Editor and Run panels.</li>
<li>Pressing the Ctrl on the Grid Editor, when over a keyword it will show its documentation (that can be detached with mouse click).</li>
<li>There are some important changes, or known issues:<ul>
<li>On Windows to call autocomplete in Grid Editor, you have to use Ctrl-Alt-Space, (or keep using Ctrl-Space after disabling Text Editor)</li>
<li>On MacOS to call autocomplete in Grid Editor, you have to use Alt-Space</li>
<li>On Linux to call autocomplete in Grid Editor, you have to use Ctrl-Space</li>
<li>On Text Editor the TAB key adds the defined number of spaces. With Shift moves to the left, and together with Control selects text.</li>
<li>On some Linuxes (Fedora, for example), when you click No in some Dialog boxes, there is the repetition of those Dialogs</li>
</ul>
</li>
</ul>
<p>(and more for you to find out ;) )</br></p>
<p><strong>THIS IS THE LAST RELEASE SUPPORTING PYTHON 2.7</strong></p>
<p><strong>wxPython will be updated to current version 4.0.6</strong></p>
<p><em>Linux users are advised to install first wxPython from .whl package at</em> <a class="reference external" href="https://extras.wxpython.org/wxPython4/extras/linux/gtk3/">wxPython.org</a>.</p>
<p>
All issues targeted for RIDE v1.7.4 can be found
from the <a class="reference external" href="https://github.com/robotframework/RIDE/issues?q=milestone%3Av1.7.4">issue tracker milestone</a>.</p>
<p>Questions and comments related to the release can be sent to the
<a class="reference external" href="http://groups.google.com/group/robotframework-users">robotframework-users</a> mailing list or to the channel #ride on
<a class="reference external" href="https://robotframework-slack-invite.herokuapp.com">Robot Framework Slack</a>, and possible bugs submitted to the <a class="reference external" href="https://github.com/robotframework/RIDE/issues">issue tracker</a>.</p>
<p>
If you have <a class="reference external" href="http://pip-installer.org">pip</a> installed, just run</p>
<pre class="literal-block">
pip install --upgrade robotframework-ride==1.7.4b2
</pre>
<p>to install this <strong>BETA</strong> release, and for the <strong>final</strong> release use</p>
<pre class="literal-block">
pip install --upgrade robotframework-ride
</pre>
<pre class="literal-block">
pip install robotframework-ride==1.7.4
</pre>
<p>to install exactly the <strong>final</strong> version. Alternatively you can download the source
distribution from <a class="reference external" href="https://pypi.python.org/pypi/robotframework-ride">PyPI</a> and install it manually. For more details and other
installation approaches, see the <a class="reference external" href="../../INSTALL.rst">installation instructions</a>.
See the <a class="reference external" href="https://github.com/robotframework/RIDE/wiki/F.A.Q.">FAQ</a> for important info about <code>: FOR</code> changes.</p>
<p>A possible way to start RIDE is:</p>
<pre class="literal-block">
python -m robotide.__init__
</pre>
<p>You can then go to <code>Tools&gt;Create RIDE Desktop Shortcut</code>, or run the shortcut creation script with:</p>
<pre class="literal-block">
python -m robotide.postinstall -install
</pre>
<p>RIDE 1.7.4b2 was released on Saturday September 7, 2019.</p>
<div class="contents local topic" id="contents">
<ul class="simple">
<li><a class="reference internal" href="#full-list-of-fixes-and-enhancements" id="id106">Full list of fixes and enhancements</a></li>
</ul>
</div>
<div class="section" id="full-list-of-fixes-and-enhancements">
<h1><a class="toc-backref" href="#id106">Full list of fixes and enhancements</a></h1>
<table border="1" class="docutils">
<colgroup>
<col width="25%" />
<col width="25%" />
<col width="10%" />
<col width="40%" />
</colgroup>
<thead valign="bottom">
<tr><th class="head">ID</th>
<th class="head">Type</th>
<th class="head">Priority</th>
<th class="head">Summary</th>
</tr>
</thead>
<tbody valign="top">
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1064">#1064</a></td>
<td>bug</td>
<td>---</td>
<td>It shows wrong Character for non-ascii characters when running</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1367">#1367</a></td>
<td>bug</td>
<td>---</td>
<td>Pressing delete in the search box on the text edit tab, deletes from the test text.</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1601">#1601</a></td>
<td>bug</td>
<td>---</td>
<td>User keyword remains on tree view after deleted from a suite</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1614">#1614</a></td>
<td>bug</td>
<td>---</td>
<td>Deleting a tag from View All Tags dialog or by deleting tag text does not remove the [Tags] section</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1739">#1739</a></td>
<td>bug</td>
<td>---</td>
<td>I'm unable to select text in cell</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1741">#1741</a></td>
<td>bug</td>
<td>---</td>
<td>Rename Test Suite always give Validation Error: Filename contains illegal characters</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1747">#1747</a></td>
<td>bug</td>
<td>---</td>
<td>RIDE-1.7.2 the Simplified-Chinese displayed problem</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1793">#1793</a></td>
<td>bug</td>
<td>---</td>
<td>Dependencies are not installed along with RIDE</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1803">#1803</a></td>
<td>bug</td>
<td>---</td>
<td>the new ride v1.7.3.1 can not support the project that chinese in path</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1804">#1804</a></td>
<td>bug</td>
<td>---</td>
<td>The new ride v1.7.3.1 can not execute by pythonw.exe</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1806">#1806</a></td>
<td>bug</td>
<td>---</td>
<td>Can't install RIDE 1.7.3.1 when using buildout</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1809">#1809</a></td>
<td>bug</td>
<td>---</td>
<td>Korean with Comment keyword makes UnicodeEncodeError .</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1812">#1812</a></td>
<td>bug</td>
<td>---</td>
<td>Unable to run test cases if # comment is commented</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1818">#1818</a></td>
<td>bug</td>
<td>---</td>
<td>I can't delete new file</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1821">#1821</a></td>
<td>bug</td>
<td>---</td>
<td>Not allowing to add or edit name of scalar variable</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1824">#1824</a></td>
<td>bug</td>
<td>---</td>
<td>Move/delete keywords doesn't show up in RIDE GUI.</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1825">#1825</a></td>
<td>bug</td>
<td>---</td>
<td>Cannot able to delete the keywords in RIDE GUI</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1826">#1826</a></td>
<td>bug</td>
<td>---</td>
<td>RIDE doesnt support new FOR loop syntax</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1845">#1845</a></td>
<td>bug</td>
<td>---</td>
<td>Grid editor issues on new RIDE</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1853">#1853</a></td>
<td>bug</td>
<td>---</td>
<td>Chinese character random code</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1857">#1857</a></td>
<td>bug</td>
<td>---</td>
<td>Duplicate save button</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1869">#1869</a></td>
<td>bug</td>
<td>---</td>
<td>Permission Issue after creating new test suite</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1870">#1870</a></td>
<td>bug</td>
<td>---</td>
<td>1.7.3.1 editor &quot;Cut&quot; is not working, the grid content is still here</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1873">#1873</a></td>
<td>bug</td>
<td>---</td>
<td>Please bring back tag wrapping</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1886">#1886</a></td>
<td>bug</td>
<td>---</td>
<td>Disabled RIDE Log plugin because of error when opened a folder</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1888">#1888</a></td>
<td>bug</td>
<td>---</td>
<td>Tags events aren't working properly</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1891">#1891</a></td>
<td>bug</td>
<td>---</td>
<td>Outdir issue with custom date</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1892">#1892</a></td>
<td>bug</td>
<td>---</td>
<td>Chinese character random code</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1895">#1895</a></td>
<td>bug</td>
<td>---</td>
<td>The keyword in Resource can't  be Rename，if you modified and saved, the system will be broken!</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1900">#1900</a></td>
<td>bug</td>
<td>---</td>
<td>Deleting a tag causes RIDE to crash</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1906">#1906</a></td>
<td>bug</td>
<td>---</td>
<td>Issues reported in google group</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1912">#1912</a></td>
<td>bug</td>
<td>---</td>
<td>On python3 there is no detection of file changes outside RIDE</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1919">#1919</a></td>
<td>bug</td>
<td>---</td>
<td>Text Editor does not update color and font size when preferences are changed</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1958">#1958</a></td>
<td>bug</td>
<td>---</td>
<td>Freeze/loading when collapsing tree</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1960">#1960</a></td>
<td>bug</td>
<td>---</td>
<td>robotframework-ride-1.7.3.1.zip lacks requirements.txt</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1967">#1967</a></td>
<td>bug</td>
<td>---</td>
<td>Ride crash when suggestion popup is shown</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1996">#1996</a></td>
<td>bug</td>
<td>---</td>
<td>Reset changes after validation</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1590">#1590</a></td>
<td>enhancement</td>
<td>---</td>
<td>Unknown variables color not documented</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1798">#1798</a></td>
<td>enhancement</td>
<td>---</td>
<td>RIDE:set default column size seems doesn't work</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1832">#1832</a></td>
<td>enhancement</td>
<td>---</td>
<td>Reopen ride，the Suite turns into Resource</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1836">#1836</a></td>
<td>enhancement</td>
<td>---</td>
<td>RIDE doesn't scroll to searched text in Text Edit view</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1837">#1837</a></td>
<td>enhancement</td>
<td>---</td>
<td>Yaml support</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1850">#1850</a></td>
<td>enhancement</td>
<td>---</td>
<td>Robot IDE - Import Errors on Startup</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1861">#1861</a></td>
<td>enhancement</td>
<td>---</td>
<td>Add a file explorer</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1904">#1904</a></td>
<td>enhancement</td>
<td>---</td>
<td>Add Reset colors button for Grid Editor preferences</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1905">#1905</a></td>
<td>enhancement</td>
<td>---</td>
<td>Add customizable colors for both Run and Text Edit in preferences</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1909">#1909</a></td>
<td>enhancement</td>
<td>---</td>
<td>RIDE does not allow to create .resource resource files extension</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1920">#1920</a></td>
<td>enhancement</td>
<td>---</td>
<td>Fixes issue <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1919">#1919</a>: Text editor update</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1921">#1921</a></td>
<td>enhancement</td>
<td>---</td>
<td>Fixes issue <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1909">#1909</a>: Added support for Resource filetype</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1926">#1926</a></td>
<td>enhancement</td>
<td>---</td>
<td>Fixes issue <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1905">#1905</a>: Added colors and font face options</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1929">#1929</a></td>
<td>enhancement</td>
<td>---</td>
<td>Alternative fix for issue <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1873">#1873</a>: No wrapping, just show a scrollbar instead</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1933">#1933</a></td>
<td>enhancement</td>
<td>---</td>
<td>No tests selected message</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1936">#1936</a></td>
<td>enhancement</td>
<td>---</td>
<td>Adds a switch to Preferences-&gt;Test Runner</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1941">#1941</a></td>
<td>enhancement</td>
<td>---</td>
<td>Made some improvements to fix from issue <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1905">#1905</a></td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1943">#1943</a></td>
<td>enhancement</td>
<td>---</td>
<td>Validation error fix</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1948">#1948</a></td>
<td>enhancement</td>
<td>---</td>
<td>Conditioned sizes of Tagboxes and ComboBoxes to be platform specific</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1966">#1966</a></td>
<td>enhancement</td>
<td>---</td>
<td>How to close text editor's auto wrap</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1969">#1969</a></td>
<td>enhancement</td>
<td>---</td>
<td>Attempt to fix app icon on Wayland. Changed robot.ico to have all sizes.</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1971">#1971</a></td>
<td>enhancement</td>
<td>---</td>
<td>[FR] Option to disable code reformatting when saving file</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1977">#1977</a></td>
<td>enhancement</td>
<td>---</td>
<td>New Parser Log tab to avoid dialog when loading Test Suite</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1980">#1980</a></td>
<td>enhancement</td>
<td>---</td>
<td>Open Files or Directories in RIDE with right-click from Files panel</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1981">#1981</a></td>
<td>enhancement</td>
<td>---</td>
<td>Update robot 3.1.2</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1994">#1994</a></td>
<td>enhancement</td>
<td>---</td>
<td>Change TAB to add spaces in Text Editor</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1805">#1805</a></td>
<td>---</td>
<td>---</td>
<td>The new ride v1.7.3.1 shortcut is not working on Windows 7</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1807">#1807</a></td>
<td>---</td>
<td>---</td>
<td>Fix <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1804">#1804</a></td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1808">#1808</a></td>
<td>---</td>
<td>---</td>
<td>Adds more files to MANIFEST, specially requirements.txt. Fixes <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1806">#1806</a></td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1819">#1819</a></td>
<td>---</td>
<td>---</td>
<td>Column sizing on Mac doesn't work.</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1838">#1838</a></td>
<td>---</td>
<td>---</td>
<td>Wip fix win encoding</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1846">#1846</a></td>
<td>---</td>
<td>---</td>
<td>Grid editor fixes</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1848">#1848</a></td>
<td>---</td>
<td>---</td>
<td>fix cells size in Grid editor</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1862">#1862</a></td>
<td>---</td>
<td>---</td>
<td>Installer - Fixes installation to all OS</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1863">#1863</a></td>
<td>---</td>
<td>---</td>
<td>Cell Sizes fixes</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1864">#1864</a></td>
<td>---</td>
<td>---</td>
<td>Installer</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1865">#1865</a></td>
<td>---</td>
<td>---</td>
<td>Desktopshortcut removal of GUI</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1866">#1866</a></td>
<td>---</td>
<td>---</td>
<td>Fixes Commented cells with # on Pause parsing</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1880">#1880</a></td>
<td>---</td>
<td>---</td>
<td>Changes encoding. Fixes running chinese path in python2.7 under Windows</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1882">#1882</a></td>
<td>---</td>
<td>---</td>
<td>Error when install v1.7.3.1 on mac</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1883">#1883</a></td>
<td>---</td>
<td>---</td>
<td>Installer</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1884">#1884</a></td>
<td>---</td>
<td>---</td>
<td>Fixes utf-8 arguments and include/exclude options in Python2.</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1889">#1889</a></td>
<td>---</td>
<td>---</td>
<td>Fix for ticket <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1888">#1888</a></td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1890">#1890</a></td>
<td>---</td>
<td>---</td>
<td>Fixes <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1824">#1824</a>. Deleted Keywords are now removed from the tree.</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1893">#1893</a></td>
<td>---</td>
<td>---</td>
<td>Fix <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1836">#1836</a></td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1897">#1897</a></td>
<td>---</td>
<td>---</td>
<td>Fix for ticket <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1739">#1739</a></td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1898">#1898</a></td>
<td>---</td>
<td>---</td>
<td>Fixes not possible to delete with Ctrl-Shift-D a commented cell</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1899">#1899</a></td>
<td>---</td>
<td>---</td>
<td>Fix for ticket <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1614">#1614</a></td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1901">#1901</a></td>
<td>---</td>
<td>---</td>
<td>Fix for ticket <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1739">#1739</a> - Fix cell select</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1902">#1902</a></td>
<td>---</td>
<td>---</td>
<td>Fix issue  <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1857">#1857</a>: Duplicate save button</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1903">#1903</a></td>
<td>---</td>
<td>---</td>
<td>Fixes issue <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1821">#1821</a>: Add or edit name</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1907">#1907</a></td>
<td>---</td>
<td>---</td>
<td>Fixes issue <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1904">#1904</a>: Reset colors button</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1908">#1908</a></td>
<td>---</td>
<td>---</td>
<td>Alternate fix for issue <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1888">#1888</a></td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1918">#1918</a></td>
<td>---</td>
<td>---</td>
<td>Fix colors</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1922">#1922</a></td>
<td>---</td>
<td>---</td>
<td>Support new &quot;For In&quot; loop syntax</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1928">#1928</a></td>
<td>---</td>
<td>---</td>
<td>Fixes issue <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1912">#1912</a>: Metaclass compatibility</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1935">#1935</a></td>
<td>---</td>
<td>---</td>
<td>Examples of Custom Scripts to use <code>maven</code> and <code>pabot</code></td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1939">#1939</a></td>
<td>---</td>
<td>---</td>
<td>Update example pom.xml</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1942">#1942</a></td>
<td>---</td>
<td>---</td>
<td>Recovers missing commit, from <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1908">#1908</a>.</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1950">#1950</a></td>
<td>---</td>
<td>---</td>
<td>Fixes permission issue</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1951">#1951</a></td>
<td>---</td>
<td>---</td>
<td>Fixes <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1832">#1832</a>:  Added default template for when new suite is created</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1954">#1954</a></td>
<td>---</td>
<td>---</td>
<td>When I delete or move use cases and keywords, ride must be restarted to display correctly.</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1959">#1959</a></td>
<td>---</td>
<td>---</td>
<td>Fixes <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1958">#1958</a>: Modified OnTreeItemCollapsing to be less recursive</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1962">#1962</a></td>
<td>---</td>
<td>---</td>
<td>Fixes some Grid resize issues</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1974">#1974</a></td>
<td>---</td>
<td>---</td>
<td>Modified OnTreeItemCollapsing to be more recursive</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1982">#1982</a></td>
<td>---</td>
<td>---</td>
<td>Change to setFocus on Windows 10</td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1991">#1991</a></td>
<td>---</td>
<td>---</td>
<td>Fix <a class="reference external" href="https://github.com/robotframework/RIDE/issues/1891">#1891</a></td>
</tr>
<tr><td><a class="reference external" href="https://github.com/robotframework/RIDE/issues/1998">#1998</a></td>
<td>---</td>
<td>---</td>
<td>Correctly keep changes if validation failed and user did not reset th…</td>
</tr>
</tbody>
</table>
<p>Altogether 105 issues. View on the <a class="reference external" href="https://github.com/robotframework/RIDE/issues?q=milestone%3Av1.7.4">issue tracker</a>.</p>
</div>

"""
