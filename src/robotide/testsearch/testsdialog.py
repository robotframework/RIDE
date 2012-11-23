#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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
from robotide.widgets import Dialog, VerticalSizer, VirtualList


class TestsDialog(Dialog):

    def __init__(self, name, tests):
        self._name = name
        self._selection_listeners = []
        title = "Tests matching '%s'" % (name)
        Dialog.__init__(self, title=title, size=(650, 400))
        self.SetSizer(VerticalSizer())
        self.tests = tests
        #TODO: Why is third header needed? - for some reason does not show second column texts without
        self.tests_list = VirtualList(self, ['Test', 'Match location', ''], self.tests)
        self.tests_list.add_selection_listener(self._usage_selected)
        self.Sizer.add_expanding(self.tests_list)

    def _usage_selected(self, idx):
        for listener in self._selection_listeners:
            listener(self.tests[idx])

    def add_selection_listener(self, listener):
        self._selection_listeners.append(listener)

    def set_focus_to_first_match(self):
        self.tests_list.Select(0)
        self.tests_list.SetFocus()
