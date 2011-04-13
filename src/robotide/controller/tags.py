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

class Tag(object):
    tooltip = "Test case's tag"

    def __init__(self, name, index=None, controller=None):
        self._name = name
        self._index = index
        self._controller = controller

    @property
    def name(self):
        return self._name

    @property
    def controller(self):
        return self._controller

    def set_index(self, index):
        self._index = index

    def is_empty(self):
        return self.name is None

    def __eq__(self, other):
        return self._name == other._name and self._index == other._index

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return self._name

    def choose(self, mapping):
        return mapping[self.__class__]


class ForcedTag(Tag):

    @property
    def tooltip(self):
        return 'Force tag from '+self._controller.source


class DefaultTag(Tag):

    @property
    def tooltip(self):
        return 'Default tag from '+self._controller.source
