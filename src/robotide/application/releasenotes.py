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
<?xml version="1.0" encoding="utf-8" ?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="generator" content="Docutils 0.15.2: http://docutils.sourceforge.net/" />
<title>Robot Framework IDE 1.7.4.1</title>
<style type="text/css">

/*
:Author: David Goodger (goodger@python.org)
:Id: $Id: html4css1.css 7952 2016-07-26 18:15:59Z milde $
:Copyright: This stylesheet has been placed in the public domain.

Default cascading style sheet for the HTML output of Docutils.

See http://docutils.sf.net/docs/howto/html-stylesheets.html for how to
customize this style sheet.
*/

/* used to remove borders from tables and images */
.borderless, table.borderless td, table.borderless th {
  border: 0 }

table.borderless td, table.borderless th {
  /* Override padding for "table.docutils td" with "! important".
     The right padding separates the table cells. */
  padding: 0 0.5em 0 0 ! important }

.first {
  /* Override more specific margin styles with "! important". */
  margin-top: 0 ! important }

.last, .with-subtitle {
  margin-bottom: 0 ! important }

.hidden {
  display: none }

.subscript {
  vertical-align: sub;
  font-size: smaller }

.superscript {
  vertical-align: super;
  font-size: smaller }

a.toc-backref {
  text-decoration: none ;
  color: black }

blockquote.epigraph {
  margin: 2em 5em ; }

dl.docutils dd {
  margin-bottom: 0.5em }

object[type="image/svg+xml"], object[type="application/x-shockwave-flash"] {
  overflow: hidden;
}

/* Uncomment (and remove this text!) to get bold-faced definition list terms
dl.docutils dt {
  font-weight: bold }
*/

div.abstract {
  margin: 2em 5em }

div.abstract p.topic-title {
  font-weight: bold ;
  text-align: center }

div.admonition, div.attention, div.caution, div.danger, div.error,
div.hint, div.important, div.note, div.tip, div.warning {
  margin: 2em ;
  border: medium outset ;
  padding: 1em }

div.admonition p.admonition-title, div.hint p.admonition-title,
div.important p.admonition-title, div.note p.admonition-title,
div.tip p.admonition-title {
  font-weight: bold ;
  font-family: sans-serif }

div.attention p.admonition-title, div.caution p.admonition-title,
div.danger p.admonition-title, div.error p.admonition-title,
div.warning p.admonition-title, .code .error {
  color: red ;
  font-weight: bold ;
  font-family: sans-serif }

/* Uncomment (and remove this text!) to get reduced vertical space in
   compound paragraphs.
div.compound .compound-first, div.compound .compound-middle {
  margin-bottom: 0.5em }

div.compound .compound-last, div.compound .compound-middle {
  margin-top: 0.5em }
*/

div.dedication {
  margin: 2em 5em ;
  text-align: center ;
  font-style: italic }

div.dedication p.topic-title {
  font-weight: bold ;
  font-style: normal }

div.figure {
  margin-left: 2em ;
  margin-right: 2em }

div.footer, div.header {
  clear: both;
  font-size: smaller }

div.line-block {
  display: block ;
  margin-top: 1em ;
  margin-bottom: 1em }

div.line-block div.line-block {
  margin-top: 0 ;
  margin-bottom: 0 ;
  margin-left: 1.5em }

div.sidebar {
  margin: 0 0 0.5em 1em ;
  border: medium outset ;
  padding: 1em ;
  background-color: #ffffee ;
  width: 40% ;
  float: right ;
  clear: right }

div.sidebar p.rubric {
  font-family: sans-serif ;
  font-size: medium }

div.system-messages {
  margin: 5em }

div.system-messages h1 {
  color: red }

div.system-message {
  border: medium outset ;
  padding: 1em }

div.system-message p.system-message-title {
  color: red ;
  font-weight: bold }

div.topic {
  margin: 2em }

h1.section-subtitle, h2.section-subtitle, h3.section-subtitle,
h4.section-subtitle, h5.section-subtitle, h6.section-subtitle {
  margin-top: 0.4em }

h1.title {
  text-align: center }

h2.subtitle {
  text-align: center }

hr.docutils {
  width: 75% }

img.align-left, .figure.align-left, object.align-left, table.align-left {
  clear: left ;
  float: left ;
  margin-right: 1em }

img.align-right, .figure.align-right, object.align-right, table.align-right {
  clear: right ;
  float: right ;
  margin-left: 1em }

img.align-center, .figure.align-center, object.align-center {
  display: block;
  margin-left: auto;
  margin-right: auto;
}

table.align-center {
  margin-left: auto;
  margin-right: auto;
}

.align-left {
  text-align: left }

.align-center {
  clear: both ;
  text-align: center }

.align-right {
  text-align: right }

/* reset inner alignment in figures */
div.align-right {
  text-align: inherit }

/* div.align-center * { */
/*   text-align: left } */

.align-top    {
  vertical-align: top }

.align-middle {
  vertical-align: middle }

.align-bottom {
  vertical-align: bottom }

ol.simple, ul.simple {
  margin-bottom: 1em }

ol.arabic {
  list-style: decimal }

ol.loweralpha {
  list-style: lower-alpha }

ol.upperalpha {
  list-style: upper-alpha }

ol.lowerroman {
  list-style: lower-roman }

ol.upperroman {
  list-style: upper-roman }

p.attribution {
  text-align: right ;
  margin-left: 50% }

p.caption {
  font-style: italic }

p.credits {
  font-style: italic ;
  font-size: smaller }

p.label {
  white-space: nowrap }

p.rubric {
  font-weight: bold ;
  font-size: larger ;
  color: maroon ;
  text-align: center }

p.sidebar-title {
  font-family: sans-serif ;
  font-weight: bold ;
  font-size: larger }

p.sidebar-subtitle {
  font-family: sans-serif ;
  font-weight: bold }

p.topic-title {
  font-weight: bold }

pre.address {
  margin-bottom: 0 ;
  margin-top: 0 ;
  font: inherit }

pre.literal-block, pre.doctest-block, pre.math, pre.code {
  margin-left: 2em ;
  margin-right: 2em }

pre.code .ln { color: grey; } /* line numbers */
pre.code, code { background-color: #eeeeee }
pre.code .comment, code .comment { color: #5C6576 }
pre.code .keyword, code .keyword { color: #3B0D06; font-weight: bold }
pre.code .literal.string, code .literal.string { color: #0C5404 }
pre.code .name.builtin, code .name.builtin { color: #352B84 }
pre.code .deleted, code .deleted { background-color: #DEB0A1}
pre.code .inserted, code .inserted { background-color: #A3D289}

span.classifier {
  font-family: sans-serif ;
  font-style: oblique }

span.classifier-delimiter {
  font-family: sans-serif ;
  font-weight: bold }

span.interpreted {
  font-family: sans-serif }

span.option {
  white-space: nowrap }

span.pre {
  white-space: pre }

span.problematic {
  color: red }

span.section-subtitle {
  /* font-size relative to parent (h1..h6 element) */
  font-size: 80% }

table.citation {
  border-left: solid 1px gray;
  margin-left: 1px }

table.docinfo {
  margin: 2em 4em }

table.docutils {
  margin-top: 0.5em ;
  margin-bottom: 0.5em }

table.footnote {
  border-left: solid 1px black;
  margin-left: 1px }

table.docutils td, table.docutils th,
table.docinfo td, table.docinfo th {
  padding-left: 0.5em ;
  padding-right: 0.5em ;
  vertical-align: top }

table.docutils th.field-name, table.docinfo th.docinfo-name {
  font-weight: bold ;
  text-align: left ;
  white-space: nowrap ;
  padding-left: 0 }

/* "booktabs" style (no vertical lines) */
table.docutils.booktabs {
  border: 0px;
  border-top: 2px solid;
  border-bottom: 2px solid;
  border-collapse: collapse;
}
table.docutils.booktabs * {
  border: 0px;
}
table.docutils.booktabs th {
  border-bottom: thin solid;
  text-align: left;
}

h1 tt.docutils, h2 tt.docutils, h3 tt.docutils,
h4 tt.docutils, h5 tt.docutils, h6 tt.docutils {
  font-size: 100% }

ul.auto-toc {
  list-style-type: none }

</style>
</head>
<body>
<div class="document" id="robot-framework-ide-1-7-4-1">
<h1 class="title">Robot Framework IDE 1.7.4.1</h1>

<p><a class="reference external" href="https://github.com/robotframework/RIDE/">RIDE (Robot Framework IDE)</a> 1.7.4.1 is a new release with bug fixes. This version 1.7.4.1 includes fixes for documentation, duplicate resources on tree, resources import with directory prefix, select all in Grid Editor, and more.
The reference for valid arguments is <a class="reference external" href="http://robotframework.org">Robot Framework</a> version 3.1.2.</p>
<ul class="simple">
<li>See the <a class="reference external" href="https://github.com/robotframework/RIDE/blob/master/doc/releasenotes/ride-1.7.4.rst">release_notes</a> for version 1.7.4 with the major changes on that version.</li>
</ul>
<p><strong>THIS IS THE LAST RELEASE SUPPORTING PYTHON 2.7</strong></p>
<p><strong>wxPython will be updated to current version 4.0.7post2</strong></p>
<p><em>Linux users are advised to install first wxPython from .whl package at</em> <a class="reference external" href="https://extras.wxpython.org/wxPython4/extras/linux/gtk3/">wxPython.org</a>.</p>
<p>All issues targeted for RIDE v1.7.4.1 can be found
from the <a class="reference external" href="https://github.com/robotframework/RIDE/issues?q=milestone%3Av1.7.4.1">issue tracker milestone</a>.</p>
<p>Questions and comments related to the release can be sent to the
<a class="reference external" href="http://groups.google.com/group/robotframework-users">robotframework-users</a> mailing list or to the channel #ride on
<a class="reference external" href="https://robotframework-slack-invite.herokuapp.com">Robot Framework Slack</a>, and possible bugs submitted to the <a class="reference external" href="https://github.com/robotframework/RIDE/issues">issue tracker</a>.</p>
<p>If you have <a class="reference external" href="http://pip-installer.org">pip</a> installed, just run</p>
<pre class="literal-block">
pip install --upgrade robotframework-ride==1.7.4.1
</pre>
<p>to upgrade to this <strong>final</strong> release, or</p>
<pre class="literal-block">
pip install --upgrade robotframework-ride
</pre>
<pre class="literal-block">
pip install robotframework-ride==1.7.4.1
</pre>
<p>to install exactly this <strong>final</strong> version for a first time. Alternatively you can download the source
distribution from <a class="reference external" href="https://pypi.python.org/pypi/robotframework-ride">PyPI</a> and install it manually. For more details and other
installation approaches, see the <a class="reference external" href="https://github.com/robotframework/RIDE/wiki/Installation-Instructions">installation instructions</a>.
See the <a class="reference external" href="https://github.com/robotframework/RIDE/wiki/F.A.Q.">FAQ</a> for important info about <code>: FOR</code> changes.</p>
<p>A possible way to start RIDE is:</p>
<pre class="literal-block">
python -m robotide.__init__
</pre>
<p>You can then go to <code>Tools&gt;Create RIDE Desktop Shortcut</code>, or run the shortcut creation script with:</p>
<pre class="literal-block">
python -m robotide.postinstall -install
</pre>
<p>RIDE 1.7.4.1 was released on Monday January 20, 2020.</p>
</div>
</body>
</html>
"""
