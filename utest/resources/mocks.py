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
import wx
import unittest
from robotide.preferences.settings import Settings
from robotide.publish import PUBLISHER


class MessageRecordingLoadObserver(object):
    def __init__(self):
        self._log = ''
        self.finished = False
        self.notified = False

    def notify(self):
        if self.finished:
            raise RuntimeError('Notified after finished')
        self.notified = True

    def finish(self):
        self.finished = True

    def error(self, msg):
        if self.finished:
            raise RuntimeError('Errored after finished')
        self.finish()
        self._log = msg

    @property
    def message(self):
        return self._log


class _FakeModel(object):
    suite = None


class _FakeActions(object):
    def register_action(self, *args):
        return self

    def unregister(self, *args):
        pass


class _FakeUIObject(object):
    Enable = InsertSeparator = Append = Connect = lambda *args: None
    Insert = FindMenu = GetMenuBar = GetMenu = lambda *args: _FakeUIObject()

    @property
    def GetMenuItemCount(self):
        return 1

    notebook = property(lambda *args: _FakeUIObject())
    actions = property(lambda *args: _FakeActions())


_FAKE_CFG_CONTENT = b'''
auto imports = []
pythonpath = []
[General]
font size = 10
font face = 'Source Code Pro'
foreground = '#8FF0A4'
background = '#A51D2D'
secondary foreground = '#FFFF00'
secondary background = '#4A060B'
background help = '#FFBE6F'
foreground text = '#613583'
apply to panels = True
ui language = 'English'
'''


class FakeSettings(Settings):
    def __init__(self, settings=None):
        self.fake_cfg = os.path.join(os.path.dirname(__file__), 'fake.cfg')
        self._default_path = self.fake_cfg
        # make sure fake cfg is clean
        with open(self.fake_cfg, 'wb') as f:
            f.write(_FAKE_CFG_CONTENT)

        Settings.__init__(self, self.fake_cfg)
        self.add_section('Plugins')
        self.set('pythonpath', [])
        self.set('auto imports', [])
        self.set('global_settings', [])
        self.set('doc language', '')
        if settings:
            for key, val in settings.items():
                self.set(key, val)


class FakeApplication(object):
    frame = _FakeUIObject()
    model = _FakeModel()
    namespace = None

    @property
    def get_model(self):
        return _FakeModel()

    @staticmethod
    def subscribe(x, y):
        return None

    @property
    def get_menu_bar(self):
        return _FakeUIObject()

    @property
    def get_notebook(self):
        return _FakeUIObject()

    @property
    def get_frame(self):
        return _FakeUIObject()

    @staticmethod
    def create_menu_item(self, *args):
        return None

    settings = FakeSettings()


class _FakeSetting(object):

    @staticmethod
    def add_section(self, name):
        return _FakeSetting()

    @staticmethod
    def get(name, default):
        return True

    @staticmethod
    def set(name, value):
        return None


class PublisherListener(object):
    def __init__(self, topic):
        PUBLISHER.subscribe(self._listener, topic)
        self._topic = topic
        self.data = []
        self.outer_listener = lambda message: 0

    def _listener(self, message):
        self.data.append(message)
        self.outer_listener(message)

    @property
    def count(self):
        return len(self.data)

    def unsubscribe(self):
        PUBLISHER.unsubscribe(self._listener, self._topic)


class FakeEditor(object):
    view = close = lambda *args: None


class UIUnitTestBase(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()

    def tearDown(self):
        # wx.CallAfter(self.app.ExitMainLoop)
        # self.app.MainLoop()
        self.app = None
