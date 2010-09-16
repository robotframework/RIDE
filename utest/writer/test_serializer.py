import StringIO
import unittest
import shutil
import tempfile
import os

from robot.parsing.model import TestCaseFile, ResourceFile
from robot.utils.asserts import assert_equals
from robotide.controller.filecontroller import ResourceFileController, \
    TestCaseFileController
from robotide.writer.serializer import Serializer


DATAPATH = os.path.join(os.path.abspath(os.path.split(__file__)[0]),
                        '..', 'resources', 'robotdata')
GOLDEN_HTML_FILE = os.path.normpath(os.path.join(DATAPATH, 'golden',
                                                   'tests.html'))


def assert_repr(first, other):
    if os.name == 'nt':
        other = other.replace('\n', '\r\n')
    return assert_equals(repr(first), repr(other))


class _TestSerializer(object):

    def get_resource_file(self):
        rf = ResourceFile()
        self._populate_setting_table(rf.setting_table)
        self._populate_variable_table(rf.variable_table)
        self._populate_keyword_table(rf.keyword_table)
        return rf

    def get_test_case_file(self):
        tcf = TestCaseFile()
        self._populate_setting_table(tcf.setting_table)
        self._populate_variable_table(tcf.variable_table)
        self._populate_keyword_table(tcf.keyword_table)
        self._populate_testcase_table(tcf.testcase_table)
        return tcf

    def _populate_setting_table(self, setting_table):
        setting_table.add_library('MyLibrary',
                                  ['argument', 'WITH NAME', 'My Alias'],
                                  comment='My library comment')
        setting_table.add_variables('MyVariables',
                                    ['args', 'args 2', 'args 3', 'args 4',
                                     'args 5', 'args 6', 'args 7', 'args 8',
                                     'args 9', 'args 10', 'args 11', 'args 12'])
        setting_table.add_resource('MyResource', 
                                   ['args that are part of the name'])

    def _populate_variable_table(self, variable_table):
        variable_table.add('MyVar', ['val1', 'val2', 'val3', 'val4', 'val5',
                                     'val6', 'val6', 'val7', 'val8', 'val9'],
                           comment='var comment')

    def _populate_keyword_table(self, keyword_table):
        kw = keyword_table.add('My Keyword')
        kw.add_step([], comment='Comment row')
        kw.add_step([], comment='Comment row 2')
        kw.add_step(['My Step 1', 'args', 'args 2', 'args 3', 'args 4',
                                 'args 5', 'args 6', 'args 7', 'args 8',
                                 'args 9'], comment='step 1 comment')
        loop = kw.add_for_loop(['${param1}', '${param2}', 'IN',
                                '${data 1}', '${data 2}', '${data 3}',
                                '${data 4}', '${data 5}', '${data 6}'])
        loop.add_step(['Loop Step', 'args', 'args 2', 'args 3', 'args 4',
                                 'args 5', 'args 6', 'args 7', 'args 8',
                                 'args 9'], comment='loop step comment')
        loop.add_step(['Loop Step 2'])
        kw.add_step(['My Step 2', 'my step 2 arg', 'second arg'],
                    comment='step 2 comment')
        kw.doc.populate('Documentation', comment='Comment for doc')
        kw.return_.populate(['args 1','args 2'])

    def _populate_testcase_table(self, testcase_table):
        tc = testcase_table.add('My Test Case')
        tc.doc.populate('This is a long comment that spans several columns')
        tc.add_step(['My TC Step 1', 'my step arg'], comment='step 1 comment')
        tc.add_step(['My TC Step 2', 'my step 2 arg', 'second arg'],
                    comment='step 2 comment')
        tc.teardown.populate(['1 minute','args'])

    def get_serialization_output(self, datafile):
        output = StringIO.StringIO()
        Serializer(output).serialize(datafile)
        return output.getvalue()


class TestTxtSerialization(unittest.TestCase, _TestSerializer):

    settings_table = '''*** Settings ***
Library         MyLibrary  argument  WITH NAME  My Alias  # My library comment
Variables       MyVariables  args  args 2  args 3  args 4  args 5  args 6
...  args 7  args 8  args 9  args 10  args 11  args 12
Resource        MyResource args that are part of the name

'''

    variables_table = '''*** Variables ***
MyVar  val1  val2  val3  val4  val5  val6  val6
...  val7  val8  val9  # var comment

'''

    keywords_table = '''*** Keywords ***
My Keyword
    [Documentation]  Documentation  # Comment for doc
    # Comment row
    # Comment row 2
    My Step 1  args  args 2  args 3  args 4  args 5  args 6  args 7
    ...  args 8  args 9  # step 1 comment
    : FOR  ${param1}  ${param2}  IN  ${data 1}  ${data 2}  ${data 3}  ${data 4}
    ...  ${data 5}  ${data 6}
    \  Loop Step  args  args 2  args 3  args 4  args 5  args 6
    ...  args 7  args 8  args 9  # loop step comment
    \  Loop Step 2
    My Step 2  my step 2 arg  second arg  # step 2 comment
    [Return]  args 1  args 2

'''

    testcase_table = '''*** Test Cases ***
My Test Case
    [Documentation]  This is a long comment that spans several columns
    My TC Step 1  my step arg  # step 1 comment
    My TC Step 2  my step 2 arg  second arg  # step 2 comment
    [Teardown]  1 minute  args

'''

    def setUp(self):
        self.txt_rf = self.get_resource_file()
        self.txt_rf.source = '/tmp/not_real_path/rf.txt'
        self.txt_tcf = self.get_test_case_file()
        self.txt_tcf.source = '/tmp/not_real_path/tcf.txt'

    def test_serializer_with_txt_resource_file(self):
        assert_repr(self.get_serialization_output(ResourceFileController(self.txt_rf)),
                      self.settings_table +
                      self.variables_table +
                      self.keywords_table)

    def test_serializer_with_txt_test_case_file(self):
        assert_repr(self.get_serialization_output(TestCaseFileController(self.txt_tcf)),
                      self.settings_table +
                      self.variables_table +
                      self.testcase_table + 
                      self.keywords_table)


class TestTsvSerialization(unittest.TestCase, _TestSerializer):

    settings_table = '''*Setting*\t*Value*\t*Value*\t*Value*\t*Value*\t*Value*\t*Value*\t*Value*
Library\tMyLibrary\targument\tWITH NAME\tMy Alias\t# My library comment\t\t
Variables\tMyVariables\targs\targs 2\targs 3\targs 4\targs 5\targs 6
...\targs 7\targs 8\targs 9\targs 10\targs 11\targs 12\t
Resource\tMyResource args that are part of the name\t\t\t\t\t\t
\t\t\t\t\t\t\t
'''

    variables_table = '''*Variable*\t*Value*\t*Value*\t*Value*\t*Value*\t*Value*\t*Value*\t*Value*
MyVar\tval1\tval2\tval3\tval4\tval5\tval6\tval6
...\tval7\tval8\tval9\t# var comment\t\t\t
\t\t\t\t\t\t\t
'''

    keywords_table = '''*Keyword*\t*Action*\t*Argument*\t*Argument*\t*Argument*\t*Argument*\t*Argument*\t*Argument*
My Keyword\t[Documentation]\tDocumentation\t# Comment for doc\t\t\t\t
\t# Comment row\t\t\t\t\t\t
\t# Comment row 2\t\t\t\t\t\t
\tMy Step 1\targs\targs 2\targs 3\targs 4\targs 5\targs 6
\t...\targs 7\targs 8\targs 9\t# step 1 comment\t\t
\t: FOR\t${param1}\t${param2}\tIN\t${data 1}\t${data 2}\t${data 3}
\t...\t${data 4}\t${data 5}\t${data 6}\t\t\t
\t\tLoop Step\targs\targs 2\targs 3\targs 4\targs 5
\t...\targs 6\targs 7\targs 8\targs 9\t# loop step comment\t
\t\tLoop Step 2\t\t\t\t\t
\tMy Step 2\tmy step 2 arg\tsecond arg\t# step 2 comment\t\t\t
\t[Return]\targs 1\targs 2\t\t\t\t
\t\t\t\t\t\t\t
'''

    testcase_table = '''*Test Case*\t*Action*\t*Argument*\t*Argument*\t*Argument*\t*Argument*\t*Argument*\t*Argument*
My Test Case\t[Documentation]\tThis is a long comment that spans several columns\t\t\t\t\t
\tMy TC Step 1\tmy step arg\t# step 1 comment\t\t\t\t
\tMy TC Step 2\tmy step 2 arg\tsecond arg\t# step 2 comment\t\t\t
\t[Teardown]\t1 minute\targs\t\t\t\t
\t\t\t\t\t\t\t
'''

    def setUp(self):
        self.tsv_rf = self.get_resource_file()
        self.tsv_rf.source = '/tmp/not_real_path/rf.tsv'
        self.tsv_tcf = self.get_test_case_file()
        self.tsv_tcf.source = '/tmp/not_real_path/tcf.tsv'

    def test_serializer_with_tsv_resource_file(self):
        assert_repr(self.get_serialization_output(ResourceFileController(self.tsv_rf)), 
                    self.settings_table +
                    self.variables_table +
                    self.keywords_table)

    def test_serializer_with_tsv_testcase_file(self):
        assert_repr(self.get_serialization_output(TestCaseFileController(self.tsv_tcf)), 
                    self.settings_table +
                    self.variables_table +
                    self.testcase_table +
                    self.keywords_table)


class TestHTMLSerialization(unittest.TestCase, _TestSerializer):
    path = os.path.join(tempfile.gettempdir(), 'ride-golden-tests.html')

    def setUp(self):
        shutil.copy(GOLDEN_HTML_FILE, self.path)

    def tearDown(self):
        os.remove(self.path)

    def test_serializer_with_html_testcase_file(self):
        original = self._read_orig()
        Serializer().serialize(TestCaseFileController(TestCaseFile(source=self.path)))
        assert_equals(original, open(self.path).read())

    def _read_orig(self):
        file = open(GOLDEN_HTML_FILE, 'r')
        original = unicode(file.read(), 'UTF-8')
        file.close()
        return original


if __name__ == "__main__":
    unittest.main()