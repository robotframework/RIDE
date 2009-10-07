import unittest
from StringIO import StringIO
from robot.utils.asserts import assert_equal, assert_true, assert_none, assert_not_none

from robotide.writer.template import _settings_re as sere
from robotide.writer.template import _variables_re as vare
from robotide.writer.template import _testcases_re as tere
from robotide.writer.template import _keywords_re as kere
from robotide.writer.template import _meta_re as mere
from robotide.writer.template import _table_replacer, _get_template


TEMPLATE = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head><meta name="rf-template" content="true"></head>
<body>
Preserved content 1.
<table id="settings"></table>
Preserved content 2.
<table id="variables" class="another attribute">Replaced content</table>
<table id='keywords'>
<tr><td>Replaced content content</td></tr>
</table>
Preserved content 3.
<table
width=30%
ID=testcases name=settings
></table>
Preserved content 4.
</body>
</html>
"""


class TestTableRegexps(unittest.TestCase):

    def test_simple_match(self):
        assert_equal(sere.search(TEMPLATE).group(), '<table id="settings"></table>')

    def test_with_table_content(self):
        assert_equal(vare.search(TEMPLATE).group(),
                     '<table id="variables" class="another attribute">Replaced content</table>')
        
    def test_match_is_case_insensitive(self):
        assert_equal(sere.match('<table id="SeTTings"></TABLE>').group(), 
                     '<table id="SeTTings"></TABLE>')

    def test_single_quotes(self):
        assert_equal(sere.match("<table id='settings'></table>").group(), 
                     "<table id='settings'></table>")

    def test_no_quotes(self):
        assert_equal(sere.match("<table id=settings foo=bar>!?</table>").group(), 
                     "<table id=settings foo=bar>!?</table>")

    def test_with_newlines_in_table_content(self):
        assert_equal(kere.search(TEMPLATE).group(), '''<table id='keywords'>
<tr><td>Replaced content content</td></tr>
</table>''')
    
    def test_with_additional_attributes(self):
        assert_equal(sere.match('<table class="before id" id="settings" width="10%"></table>').group(), 
                     '<table class="before id" id="settings" width="10%"></table>')

    def test_with_newline_in_start_tag(self):
        assert_equal(tere.search(TEMPLATE).group(),
                     '<table\nwidth=30%\nID=testcases name=settings\n></table>')


class TestSubstitution(unittest.TestCase):
    
    def test_simple_substitution(self):
        repl = _table_replacer('content')
        assert_equal(sere.sub(repl, 'before<table id="settings"></table>after'),
                     'before<table id="settings">\ncontent\n</table>after')

    def test_empty_content(self):
        repl = _table_replacer('')
        assert_equal(vare.sub(repl, 'B<TABLE ID=VARIABLES>\nOLD\n</TABLE>A'),
                     'B<TABLE ID=VARIABLES>\n</TABLE>A')

    def test_stripping_whitespace_from_content(self):
        repl = _table_replacer('\n\nSTUFF\nIN TWO LINES   \n\n')
        assert_equal(tere.sub(repl, '<table a="1" id="testcases"></table>'),
                     '<table a="1" id="testcases">\nSTUFF\nIN TWO LINES\n</table>')

    def test_substitution(self):
        actual = TEMPLATE
        for regexp, content in [ (sere, 'SETTINGS'), (vare, 'ROW 1\nROW 2'),
                                 (kere, ''), (tere, 'TC1\nTC2\nTC3') ]:
            actual = regexp.sub(_table_replacer(content), actual)
        assert_equal(actual, """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head><meta name="rf-template" content="true"></head>
<body>
Preserved content 1.
<table id="settings">
SETTINGS
</table>
Preserved content 2.
<table id="variables" class="another attribute">
ROW 1
ROW 2
</table>
<table id='keywords'>
</table>
Preserved content 3.
<table
width=30%
ID=testcases name=settings
>
TC1
TC2
TC3
</table>
Preserved content 4.
</body>
</html>
""")


class TestTemplateRecognition(unittest.TestCase):

    def test_no_matching_meta(self):
        for inp in ['', '<html></html>', '<meta name="rf-template" foo="bar">'
                    '<html><head><meta name="foo" content="bar"></head></html>']: 
            assert_none(mere.search(inp))

    def test_simple_match(self):
        self._verify_match('<meta name="rf-template" content="true">')

    def test_match_is_case_insensitive(self):
        self._verify_match('<META Name="RF-Template" content="True">')

    def test_optional_trailing_slash(self):
        self._verify_match('<meta name="rf-template" content="true"/>')
        self._verify_match('<meta name="rf-template" content="true" />')

    def test_whitespace(self):
        self._verify_match('<meta\nname="rf-template"         \tcontent="true"\n>')

    def test_test_quotes(self):
        self._verify_match("<meta name='rf-template' content='true'>")
        self._verify_match('<meta name=rf-template content=true>')

    def test_attribute_order(self):
        self._verify_match('<meta content="true" name="rf-template">')
        self._verify_match('<meta content="true"\n name=rf-template/>')

    def test_meta_must_be_inside_head_tag(self):
        assert_none(mere.search('<meta name="rf-template" content="true">'))

    def test_other_head_content(self):
        self._verify_match('<meta foo="bar">\n<meta name="rf-template" content="true">\t<style />')

    def test_get_template_returns_recognized_template(self):
        assert_equal(TEMPLATE, _get_template(StringIO(TEMPLATE), default_template=None))

    def test_get_template_returns_default_template_when_no_recognition(self):
        for inp in ['', 'hello world', TEMPLATE.replace('<meta', ''),
                    TEMPLATE.replace('</head>', '')]:
            result = _get_template(StringIO(inp), default_template='default')
            assert_equal(result, 'default')

    def _verify_match(self, inp):
        inp = '<head>%s</head>' % inp
        assert_not_none(mere.search(inp))
        assert_equal(inp, _get_template(StringIO(inp), default_template=None))


if __name__ == '__main__':
    unittest.main()
