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

from ..controller.basecontroller import _BaseController


class Tag(_BaseController):
    tooltip = "Own tag"

    def __init__(self, name, index=None, controller=None):
        self.name = name
        self.controller = controller
        self.index = index

    def set_index(self, index):
        self.index = index

    def is_empty(self):
        return self.name is None

    def __eq__(self, other):
        return self.name == other.name and self.index == other.index

    def __ne__(self, other):
        return not (self == other)  # This cannot be compared with !=

    def __str__(self):
        return self.name

    def choose(self, mapping):
        return mapping[self.__class__]

    def delete(self):
        self.controller.remove(str(self.name))
        if type(self) is Tag and len(self.controller.tags.value) == 0:
            if len(self.controller.parent.default_tags.value) > 0:
                self.controller.set_value("")
            else:
                self.controller.clear_field()


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


class TestTag(Tag):

    @property
    def tooltip(self):
        return u'Apply Test Tags from suite {0} (since Robot Framework 6.0)'.format(
            self.controller.datafile_controller.name)
