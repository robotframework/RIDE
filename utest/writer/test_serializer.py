'''
Created on Jun 7, 2010

@author: Jussi Malinen
'''
from robot.parsing.model import TestCaseFile, ResourceFile
from robotide.writer.serializer import Serializer
import StringIO
import unittest
from robot.utils.asserts import assert_equal

class TestSerializer(unittest.TestCase):

    def setUp(self):
        self.setUpTxtResourceFile()
        self.setUpTxtTestCaseFile()

    def setUpTxtResourceFile(self):
        self.rf = ResourceFile()
        self.rf.source = '/tmp/not_existing_path/resource.txt'
        self.rf.setting_table.add_library('MyLibrary', 
                                          ['argument', 'WITH NAME', 'My Alias'],
                                          comment='My library comment')
        self.rf.setting_table.add_variables('MyVariables', 
                                            ['args', 'args 2'])
        self.rf.setting_table.add_resource('MyResource', 
                                           ['args that are part of the name'])
        self.rf.variable_table.add('MyVar', ['val1', 'val2'], 
                                   comment='var comment')
        kw = self.rf.keyword_table.add('My Keyword')
        kw.add_step(['My Step 1', 'my step arg'], comment='step 1 comment')
        kw.add_step(['My Step 2', 'my step 2 arg', 'second arg'], 
                    comment='step 2 comment')
        kw.doc.set('Documentation', comment='Comment for doc')
        kw.return_.set(['args 1','args 2'])

    def set_up_txt_test_case_file(self):
        self.tcf = TestCaseFile()
        self.tcf.source = '/tmp/not_existing_path/tcf.txt'
        self.tcf.setting_table.add_library('MyLibrary', 
                                          ['argument', 'WITH NAME', 'My Alias'],
                                          comment='My library comment')
        self.tcf.setting_table.add_variables('MyVariables', 
                                            ['args', 'args 2'])
        self.tcf.setting_table.add_resource('MyResource', 
                                           ['args that are part of the name'])
        self.tcf.variable_table.add('MyVar', ['val1', 'val2'], 
                                   comment='var comment')
        kw = self.tcf.keyword_table.add('My Keyword')
        kw.add_step(['My Step 1', 'my step arg'], comment='step 1 comment')
        kw.add_step(['My Step 2', 'my step 2 arg', 'second arg'], 
                    comment='step 2 comment')
        tc = self.tcf.testcase_table.add('My Test Case')
        tc.add_step(['My TC Step 1', 'my step arg'], comment='step 1 comment')
        tc.add_step(['My TC Step 2', 'my step 2 arg', 'second arg'], 
                    comment='step 2 comment')
        tc.teardown.set(['1 minute','args'])
        

    def test_serializer_with_txt_resource_file(self):
        output = StringIO.StringIO()
        serializer = Serializer(output)
        serializer.serialize(self.rf)
        assert_equal(output.getvalue(),
'''*** Settings ***
# My library comment
Library  MyLibrary  argument  WITH NAME  My Alias
Variables  MyVariables  args  args 2
Resource  MyResource args that are part of the name

*** Variables ***
# var comment
MyVar  val1  val2

*** Keywords ***
My Keyword
    # Comment for doc
    [Documentation]  Documentation
    [Return]  args 1  args 2
    # step 1 comment
    My Step 1  my step arg
    # step 2 comment
    My Step 2  my step 2 arg  second arg

''')

    def test_serializer_with_txt_test_case_file(self):
        output = StringIO.StringIO()
        serializer = Serializer(output)
        serializer.serialize(self.tcf)
        assert_equal(output.getvalue(),
'''*** Settings ***
# My library comment
Library  MyLibrary  argument  WITH NAME  My Alias
Variables  MyVariables  args  args 2
Resource  MyResource args that are part of the name

*** Variables ***
# var comment
MyVar  val1  val2

*** Test Cases ***
My Test Case
    # step 1 comment
    My TC Step 1  my step arg
    # step 2 comment
    My TC Step 2  my step 2 arg  second arg
    [Teardown]  1 minute  args

*** Keywords ***
My Keyword
    # step 1 comment
    My Step 1  my step arg
    # step 2 comment
    My Step 2  my step 2 arg  second arg

''')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()