#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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
import sys

from robotide.version import VERSION
from robotide.robotapi import ROBOT_LOGGER, ROBOT_VERSION

from font import Font
from logger import Logger
from settings import Settings, initialize_settings
from coreplugins import get_core_plugins
from platform import IS_MAC, IS_WINDOWS, ctrl_or_cmd, bind_keys_to_evt_menu


class RideSettings(Settings):

    def __init__(self):
        default_path = os.path.join(os.path.dirname(__file__), 'settings.cfg')
        user_path = initialize_settings('ride', default_path)
        Settings.__init__(self, user_path)
        self._settings_dir = os.path.dirname(user_path)
        self.set('install root', os.path.dirname(os.path.dirname(__file__)))

    def get_path(self, *parts):
        """Returns path which combines settings directory and given parts."""
        return os.path.join(self._settings_dir, *parts)


SETTINGS = RideSettings()
for path in SETTINGS['pythonpath']:
    sys.path.insert(0, path.replace('/', os.sep))

LOG = Logger()
ROBOT_LOGGER.disable_automatic_console_logger()
ROBOT_LOGGER.register_logger(LOG)

SETTING_EDITOR_WIDTH = 450
SETTING_LABEL_WIDTH = 150
SETTING_ROW_HEIGTH = 25
POPUP_BACKGROUND = (255, 255, 187)

pyversion = '.'.join(str(v) for v in sys.version_info[:3])
ABOUT_RIDE = '''<h3>RIDE -- Robot Framework Test Data Editor</h3>
<p>Version %s running on Python %s using Robot Framework %s.</p>
<p>Documentation, issue tracker and other information can be found from the project pages at
<a href="http://code.google.com/p/robotframework-ride">http://code.google.com/p/robotframework-ride</a>.</p>
<p>Part of the used icons are from Silk Icons <a href="http://www.famfamfam.com/lab/icons/silk/">http://www.famfamfam.com/lab/icons/silk/</a>.
''' % (VERSION, pyversion, ROBOT_VERSION)

APP = None
