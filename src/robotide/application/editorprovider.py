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

class EditorProvider(object):

    def __init__(self):
        self._editors = {}

    def register_editor(self, key, editor, default=True):
        if key not in self._editors:
            self._editors[key] = _EditorList()
        self._editors[key].add(editor, default)

    def unregister_editor(self, key, editor):
        self._editors[key].remove(editor)

    def set_active_editor(self, key, editor):
        self._editors[key].set_default(editor)

    def get_editor(self, key):
        return self._editors[key].get()

    def get_editors(self, key):
        return self._editors[key].get_all()


class _EditorList(object):

    def __init__(self):
        self._editors = []

    def add(self, editor, default=True):
        if editor in self._editors:
            return
        if default:
            self._editors.append(editor)
        else:
            self._editors.insert(0, editor)

    def set_default(self, editor):
        if self._editors.index(editor) != -1:
            self._editors.remove(editor)
            self._editors.append(editor)

    def remove(self, editor):
        self._editors.remove(editor)

    def get(self):
        return self._editors[-1]

    def get_all(self):
        return self._editors
