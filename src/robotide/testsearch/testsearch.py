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
from robotide.pluginapi import Plugin
from robotide.widgets import ImageProvider


class TestSearchPlugin(Plugin):

    def enable(self):
        self.register_search_action('Search Tests', self.show_search_for, ImageProvider().TEST_SEARCH_ICON)

    def show_search_for(self, text):
        def etsii(data):
            for t in data.tests:
                if text in t.name or text in [str(tag) for tag in t.tags]:
                    print t.longname
            for s in data.suites:
                etsii(s)
        etsii(self.frame._controller.data)

