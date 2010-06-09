'''
Created on Jun 7, 2010

@author: Jussi Malinen
'''
from robot.parsing.model import TestCaseFile, ResourceFile
from robot.utils.asserts import assert_equals
from robotide.writer.serializer import Serializer, _WriterSerializer
from robotide.writer.writer import HtmlFileWriter
import StringIO
import unittest

def assert_repr(first, other):
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
Variables       MyVariables  args  args 2
Resource        MyResource args that are part of the name

'''

    variables_table = '''*** Variables ***
MyVar  val1  val2  val3  val4  val5  val6  val6
...  val7  val8  val9  # var comment

'''

    keywords_table = '''*** Keywords ***
My Keyword
    [Documentation]  Documentation  # Comment for doc
    [Return]  args 1  args 2
    # Comment row
    # Comment row 2
    My Step 1  my step arg  # step 1 comment
    My Step 2  my step 2 arg  second arg  # step 2 comment

'''

    testcase_table = '''*** Test Cases ***
My Test Case
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
        assert_equals(self.get_serialization_output(self.txt_rf),
                      self.settings_table +
                      self.variables_table +
                      self.keywords_table)

    def test_serializer_with_txt_test_case_file(self):
        assert_equals(self.get_serialization_output(self.txt_tcf),
                      self.settings_table +
                      self.variables_table +
                      self.testcase_table + 
                      self.keywords_table)


class TestTsvSerialization(unittest.TestCase, _TestSerializer):

    settings_table = '''*Setting*\t*Value*\t*Value*\t*Value*\t*Value*\t*Value*\t*Value*\t*Value*
# My library comment\t\t\t\t\t\t\t
Library\tMyLibrary\targument\tWITH NAME\tMy Alias\t\t\t
Variables\tMyVariables\targs\targs 2\t\t\t\t
Resource\tMyResource args that are part of the name\t\t\t\t\t\t
\t\t\t\t\t\t\t
'''

    variables_table = '''*Variable*\t*Value*\t*Value*\t*Value*\t*Value*\t*Value*\t*Value*\t*Value*
# var comment\t\t\t\t\t\t\t
MyVar\tval1\tval2\tval3\tval4\tval5\tval6\tval6
...\tval7\tval8\tval9\t\t\t\t\n\t\t\t\t\t\t\t
'''

    keywords_table = '''*Keyword*\t*Action*\t*Argument*\t*Argument*\t*Argument*\t*Argument*\t*Argument*\t*Argument*
# Comment for doc\t\t\t\t\t\t\t
My Keyword\t[Documentation]\tDocumentation\t\t\t\t\t
\t[Return]\targs 1\targs 2\t\t\t\t
# step 1 comment\t\t\t\t\t\t\t
\tMy Step 1\tmy step arg\t\t\t\t\t
# step 2 comment\t\t\t\t\t\t\t
\tMy Step 2\tmy step 2 arg\tsecond arg\t\t\t\t
\t\t\t\t\t\t\t
'''

    testcase_table = '''*Test Case*\t*Action*\t*Argument*\t*Argument*\t*Argument*\t*Argument*\t*Argument*\t*Argument*
# step 1 comment\t\t\t\t\t\t\t
My Test Case\tMy TC Step 1\tmy step arg\t\t\t\t\t
# step 2 comment\t\t\t\t\t\t\t
\tMy TC Step 2\tmy step 2 arg\tsecond arg\t\t\t\t
\t[Teardown]\t1 minute\targs\t\t\t\t
\t\t\t\t\t\t\t
'''

    def setUp(self):
        self.tsv_rf = self.get_resource_file()
        self.tsv_rf.source = '/tmp/not_real_path/rf.tsv'
        self.tsv_tcf = self.get_test_case_file()
        self.tsv_tcf.source = '/tmp/not_real_path/tcf.tsv'

    def test_serializer_with_tsv_resource_file(self):
        assert_repr(self.get_serialization_output(self.tsv_rf), 
                    self.settings_table +
                    self.variables_table +
                    self.keywords_table)

    def test_serializer_with_tsv_testcase_file(self):
        assert_repr(self.get_serialization_output(self.tsv_tcf), 
                    self.settings_table +
                    self.variables_table +
                    self.testcase_table +
                    self.keywords_table)


class TestHTMLSerialization(unittest.TestCase, _TestSerializer):

    def setUp(self):
        self.html_rf = self.get_resource_file()
        self.html_rf.source = '/tmp/not_real_path/rf.html'
        self.html_tcf = self.get_test_case_file()
        self.html_tcf.source = '/tmp/not_real_path/tcf.html'

    def test_serializer_with_html_resource_file(self):
        #assert_repr(self.get_serialization_output(self.html_rf), 'g')
        #output = StringIO.StringIO()
        #writer = HtmlFileWriter(output, path=None)
        #_WriterSerializer(writer).serialize(self.html_rf)
        #assert_equals(writer._content, 'd')
        pass

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()