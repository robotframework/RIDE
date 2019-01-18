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

from robotide.controller.basecontroller import _BaseController
from robotide.utils import PY3
if PY3:
    from robotide.utils import unicode


class Tag(_BaseController):
    tooltip = "Own tag"

    def __init__(self, name, index=None, controller=None):
        self.name = name
        self.controller = controller
        self._index = index

    def set_index(self, index):
        self._index = index

    def is_empty(self):
        return self.name is None

    def __eq__(self, other):
        return self.name == other.name and self._index == other._index

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return self.name

    def choose(self, mapping):
        return mapping[self.__class__]

    def delete(self):
        self.controller.remove(unicode(self.name))
        if type(self) is Tag and len(self.controller._tags.value) == 0:
            if len(self.controller.parent.default_tags.value) > 0:
                self.controller.set_value("")
            else:
                self.controller.clear()


class ForcedTag(Tag):

    @property
    def tooltip(self):
        return u'Force tag from suite {0}'.format(
            self.controller.datafile_controller.name)


class DefaultTag(Tag):

    @property
    def tooltip(self):
        return u'Default tag from suite {0}'.format(
            self.controller.datafile_controller.name)
