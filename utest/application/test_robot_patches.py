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

import unittest

from robotide.robotapi import Timeout, Tags, Fixture, Template


class Test(unittest.TestCase):

    def test_timeout_patch(self):
        timeout = Timeout('Timeout')
        assert timeout.as_list() ==['Timeout']
        timeout.message='boo'
        assert timeout.as_list() ==['Timeout', '', 'boo']
        timeout.message=''
        timeout.value='1 second'
        assert timeout.as_list() ==['Timeout', '1 second']
        timeout.message='boo'
        assert timeout.as_list() ==['Timeout', '1 second', 'boo']

    def test_settings_patch(self):
        tags = Tags('Tags')
        assert tags.as_list() ==['Tags']
        tags.value = ['tag1','tag2']
        assert tags.as_list() ==['Tags', 'tag1', 'tag2']

    def test_fixture_patch(self):
        fixture = Fixture('Teardown')
        assert fixture.as_list() == ['Teardown']
        fixture.name = 'Keyword'
        assert fixture.as_list() == ['Teardown', 'Keyword']
        fixture.args = ['arg1', 'arg2']
        assert fixture.as_list() == ['Teardown', 'Keyword', 'arg1', 'arg2']
        fixture.name = ''
        assert fixture.as_list() == ['Teardown', '', 'arg1', 'arg2']

    def test_template_patch(self):
        template = Template('Template')
        assert template.as_list() ==['Template']
        template.value = 'value'
        assert template.as_list() ==['Template', 'value']


if __name__ == "__main__":
    unittest.main()
