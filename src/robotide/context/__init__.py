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

import sys

from robotide.version import VERSION
from robotide.robotapi import ROBOT_LOGGER

from coreplugins import get_core_plugins
from logger import Logger
from platform import (IS_MAC, IS_WINDOWS, WX_VERSION, ctrl_or_cmd,
    bind_keys_to_evt_menu)
LOG = Logger()
ROBOT_LOGGER.disable_automatic_console_logger()
ROBOT_LOGGER.register_logger(LOG)

SETTING_EDITOR_WIDTH = 450
SETTING_LABEL_WIDTH = 150
SETTING_ROW_HEIGTH = 25
POPUP_BACKGROUND = (255, 255, 187)

pyversion = '.'.join(str(v) for v in sys.version_info[:3])
SYSTEM_INFO = "Started RIDE %s using python version %s with wx version %s in %s." % \
        (VERSION, pyversion, WX_VERSION, sys.platform)
ABOUT_RIDE = '''<h3>RIDE -- Robot Framework Test Data Editor</h3>
<p>RIDE %s running on Python %s.</p>
<p>RIDE is a test data editor for <a href="http://robotframework.org">Robot Framework</a>.
For more information, see project pages at
<a href="http://github.com/robotframework/RIDE">http://github.com/robotframework/RIDE</a>.</p>
<p>Some of the icons are from <a href="http://www.famfamfam.com/lab/icons/silk/">Silk Icons</a>.</p>
''' % (VERSION, pyversion)
SHORTCUT_KEYS = '''<h2>Shortcut keys in RIDE</h2>
<table>
    <tr align="left">
        <th><b>Shortcut</b></th>
        <th><b>What it does</b></th>
    </tr>
    <tr>
        <td>CtrlCmd-S</td>
        <td>Save</td>
    </tr>
    <tr>
        <td>CtrlCmd-Shift-S</td>
        <td>Save all</td>
    </tr>
    <tr>
        <td>CtrlCmd-O</td>
        <td>Open</td>
    </tr>
    <tr>
        <td>CtrlCmd-Shift-O</td>
        <td>Open directory</td>
    </tr>
    <tr>
        <td>CtrlCmd-R</td>
        <td>Open resource</td>
    </tr>
    <tr>
        <td>CtrlCmd-Shift-R</td>
        <td>Refresh directory</td>
    </tr>
    <tr>
        <td>CtrlCmd-N</td>
        <td>New project</td>
    </tr>
    <tr>
        <td>CtrlCmd-Shift-N</td>
        <td>New resource</td>
    </tr>
    <tr>
        <td>CtrlCmd-Q</td>
        <td>Quit RIDE</td>
    </tr>
    <tr>
        <td>Alt-X</td>
        <td>Go Forward</td>
    </tr>
    <tr>
        <td>Alt-Z</td>
        <td>Go Back</td>
    </tr>
    <tr>
        <td>F6</td>
        <td>Open preview</td>
    </tr>
    <tr>
        <td>F5</td>
        <td>Open search keywords dialog</td>
    </tr>
    <tr>
        <td>F8</td>
        <td>Run test suite</td>
    </tr>
    <tr>
        <td>CtrlCmd-F8</td>
        <td>Stop running test suite</td>
    </tr>
</table>
<h3>Grid</h3>

<table>
    <tr align="left">
        <th><b>Shortcut</b></th>
        <th><b>What it does</b></th>
    </tr>
    <tr>
        <td>Ctrl-Space</td>
        <td>Suggestions and auto completion</td>
    </tr>
    <tr>
        <td>CtrlCmd-I</td>
        <td>Insert row(s)</td>
    </tr>
    <tr>
        <td>CtrlCmd-D</td>
        <td>Remove row(s)</td>
    </tr>
    <tr>
        <td>CtrlCmd-Z</td>
        <td>Undo</td>
    </tr>
    <tr>
        <td>CtrlCmd-Y</td>
        <td>Redo</td>
    </tr>
    <tr>
        <td>CtrlCmd-3</td>
        <td>Comment row(s)</td>
    </tr>
    <tr>
        <td>CtrlCmd-4</td>
        <td>Uncomment row(s)</td>
    </tr>
    <tr>
        <td>Alt-Up</td>
        <td>Move row(s) up</td>
    </tr>
    <tr>
        <td>Alt-Down</td>
        <td>Move row(s) down</td>
    </tr>
    <tr>
        <td>CtrlCmd-A</td>
        <td>Select all</td>
    </tr>
    <tr>
        <td>CtrlCmd-X</td>
        <td>Cut (does not remove cells or rows)</td>
    </tr>
    <tr>
        <td>CtrlCmd-C</td>
        <td>Copy</td>
    </tr>
    <tr>
        <td>CtrlCmd-V</td>
        <td>Paste (does not move cells or rows)</td>
    </tr>
    <tr>
        <td>CtrlCmd-Shift-V</td>
        <td>Insert (adds empty rows and pastes data)</td>
    </tr>
    <tr>
        <td>Delete</td>
        <td>Remove cell content</td>
    </tr>
</table>

<h3>Tree view</h3>
<table>
    <tr align="left">
        <th><b>Shortcut</b></th>
        <th><b>What it does</b></th>
    </tr>
    <tr>
        <td>CtrlCmd-Shift-T</td>
        <td>Add new test case</td>
    </tr>
    <tr>
        <td>CtrlCmd-Shift-K</td>
        <td>Add new keyword</td>
    </tr>
    <tr>
        <td>CtrlCmd-Shift-V</td>
        <td>Add new scalar variable</td>
    </tr>
    <tr>
        <td>CtrlCmd-Shift-L</td>
        <td>Add new list variable</td>
    </tr>
    <tr>
        <td>F2</td>
        <td>Rename</td>
    </tr>
    <tr>
        <td>CtrlCmd-Shift-C</td>
        <td>Clone/Copy selected keyword/test case</td>
    </tr>
    <tr>
        <td>CtrlCmd-Up</td>
        <td>Move item up</td>
    </tr>
    <tr>
        <td>CtrlCmd-Down</td>
        <td>Move item down</td>
    </tr>
</table>
'''

APP = None
