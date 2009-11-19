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


import os.path

from robotide.version import VERSION

from logger import Logger
from robotide.robotapi import ROBOT_LOGGER
from settings import Settings, initialize_settings


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

LOG = Logger()
ROBOT_LOGGER.disable_automatic_console_logger()
ROBOT_LOGGER.register_logger(LOG)

SETTING_EDITOR_WIDTH = 450
SETTING_LABEL_WIDTH = 175
SETTING_ROW_HEIGTH = 25
POPUP_BACKGROUND = (255, 255, 187)

ABOUT_RIDE = '''<h3>RIDE, version %s</h3>
<p>More information in <a href=http://code.google.com/p/robotframework-ride/>project pages</a>.</p>
<p>Contact developers <a href="mailto:robotframework-devel@googlegroups.com">
robotframework-devel@googlegroups.com</a>''' % VERSION

APP = None
