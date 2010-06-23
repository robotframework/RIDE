#  Copyright 2008 Nokia Siemens Networks Oyj
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

from StringIO import StringIO


class MessageRecordingLoadObserver(object):
    def __init__(self):
        self._log = StringIO()
        self.finish_called = False

    def notify(self):
        pass

    def finished(self):
        self.finish_called = True

    def error(self, msg):
        self.finished()
        self._log.write(msg)

    @property
    def message(self):
        return self._log.getvalue()


class _FakeModel(object):
    suite = None

class _FakeUIObject(object):
    Enable = InsertSeparator = Append = Connect = lambda *args: None
    Insert = FindMenu = GetMenuBar = GetMenu = lambda *args: _FakeUIObject()
    GetMenuItemCount = lambda s: 1
    notebook = property(lambda *args: _FakeUIObject())

class FakeApplication(object):
    frame = _FakeUIObject()
    model = _FakeModel()
    namespace = None
    get_model = lambda s: _FakeModel()
    subscribe = lambda s, x, y: None
    get_menu_bar = lambda s: _FakeUIObject()
    get_notebook = lambda s: _FakeUIObject()
    get_frame = lambda s: _FakeUIObject()
    create_menu_item = lambda *args: None

class FakeSettings(object):
    def __getitem__(self, name):
        return _FakeSetting()

class _FakeSetting(object):
    add_section = lambda self, name: _FakeSetting()
    get = lambda self, name, deafault: True
    set = lambda self, name, value: None
