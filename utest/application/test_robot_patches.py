from nose.tools import assert_equals
import unittest

from robotide.robotapi import Timeout, Tags, Fixture, Template


class Test(unittest.TestCase):

    def test_timeout_patch(self):
        timeout = Timeout('Timeout')
        assert_equals(timeout.as_list(),['Timeout'])
        timeout.message='boo'
        assert_equals(timeout.as_list(),['Timeout', '', 'boo'])
        timeout.message=''
        timeout.value='1 second'
        assert_equals(timeout.as_list(),['Timeout', '1 second'])
        timeout.message='boo'
        assert_equals(timeout.as_list(),['Timeout', '1 second', 'boo'])

    def test_settings_patch(self):
        tags = Tags('Tags')
        assert_equals(tags.as_list(),['Tags'])
        tags.value = ['tag1','tag2']
        assert_equals(tags.as_list(),['Tags', 'tag1', 'tag2'])

    def test_fixture_patch(self):
        fixture = Fixture('Teardown')
        assert_equals(fixture.as_list(), ['Teardown'])
        fixture.name = 'Keyword'
        assert_equals(fixture.as_list(), ['Teardown', 'Keyword'])
        fixture.args = ['arg1', 'arg2']
        assert_equals(fixture.as_list(), ['Teardown', 'Keyword', 'arg1', 'arg2'])
        fixture.name = ''
        assert_equals(fixture.as_list(), ['Teardown', '', 'arg1', 'arg2'])

    def test_template_patch(self):
        template = Template('Template')
        assert_equals(template.as_list(),['Template'])
        template.value = 'value'
        assert_equals(template.as_list(),['Template', 'value'])


if __name__ == "__main__":
    unittest.main()
