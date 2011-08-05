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
from robotide.publish.messages import RideMessage


class RideTreeAwarePluginAdded(RideMessage):
    data = ['plugin']

class TreeAwarePluginMixin(object):

    _tree_aware_plugins_set = None

    def is_focus_on_tree_aware_plugin(self):
        return any(twb.is_focused() for twb in self._tree_aware_plugins)

    def add_self_as_tree_aware_plugin(self):
        RideTreeAwarePluginAdded(plugin=self).publish()
        self.subscribe(self._tree_aware_plugin_added, RideTreeAwarePluginAdded)

    def remove_self_from_tree_aware_plugins(self):
        self.unsubscibe(self._tree_aware_plugin_added, RideTreeAwarePluginAdded)
        for other in self._tree_aware_plugins:
            other.remove_tree_aware_plugin(self)

    def add_tree_aware_plugin(self, other):
        self._tree_aware_plugins.add(other)

    def remove_tree_aware_plugin(self, other):
        self._tree_aware_plugins.remove(other)

    def _tree_aware_plugin_added(self, message=None):
        self.add_tree_aware_plugin(message.plugin)
        message.plugin.add_tree_aware_plugin(self)

    @property
    def _tree_aware_plugins(self):
        if self._tree_aware_plugins_set is None:
            self._tree_aware_plugins_set = set()
        return self._tree_aware_plugins_set
