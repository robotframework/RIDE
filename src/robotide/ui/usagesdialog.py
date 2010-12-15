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

from robotide.widgets import Dialog, List, VerticalSizer


class UsagesDialog(Dialog):

    def __init__(self, name, usages):
        self._selection_listeners = []
        self.usages = list(usages)
        usage_labels = [[u.usage, u.datafile.name] for u in self.usages]
        Dialog.__init__(self, "'%s' - %d usages"
                                    % (name, len(usage_labels)))
        self.SetSizer(VerticalSizer())
        usage_list = List(self, ['Usage', 'Source'], usage_labels)
        usage_list.add_selection_listener(self._usage_selected)
        self.Sizer.add_expanding(usage_list)

    def _usage_selected(self, idx):
        for listener in self._selection_listeners:
            listener(self.usages[idx].item.parent)

    def add_selection_listener(self, listener):
        self._selection_listeners.append(listener)
