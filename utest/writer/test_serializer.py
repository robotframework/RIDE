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
        self.rf = ResourceFile()
        self.rf.source = '/tmp/not_existing_path/resource.txt'
        self.rf.setting_table.add_library('MyLibrary', 
                                          ['argument', 'WITH NAME', 'My Alias'],
                                          comment='My library comment')
        self.rf.setting_table.add_variables('MyVariables', ['args'])
        self.rf.setting_table.add_resource('MyResource', ['args'])
        self.rf.variable_table.add('MyVar', ['val1', 'val2'], 
                                   comment='var comment')
        kw = self.rf.keyword_table.add('My Keyword')
        kw.add_step(['my step', 'my step arg'], comment='step 1 comment')

    def testCreateSerializerWithCustomOutput(self):
        output = StringIO.StringIO()
        serializer = Serializer(output)
        serializer.serialize(self.rf)
        assert_equal(output.getvalue(),
'''*** Settings ***
# My library comment
Library         MyLibrary  argument  WITH NAME  My Alias
Variables       MyVariables  args
Resource        MyResource args

*** Variables ***
# var comment
MyVar  val1  val2

*** Keywords ***
My Keyword
    # step 1 comment
    my step  my step arg

''')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()