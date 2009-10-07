#  Copyright 2008 Nokia Siemens Networks Oyj
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

from robotide.model.files import TestSuiteFactory
from resources import COMPLEX_SUITE_PATH, MockSerializer
from robot.utils.asserts import assert_equals


class TestSerialization(unittest.TestCase):
    
    def test_test_suite_serializing(self):
        suite = TestSuiteFactory(COMPLEX_SUITE_PATH)
        serializer = MockSerializer()
        suite._serialize(serializer)
        exp = ['Start Settings', 
               "Setting: Documentation | [u'This test data file is used in *RobotIDE* _integration_ tests.']", 
               "Setting: Default Tags | [u'regeression']", 
               "Setting: Force Tags | [u'ride']", 
               "Setting: Suite Setup | [u'My Suite Setup']", 
               "Setting: Suite Teardown | [u'My Suite Teardown', u'${scalar}', u'@{LIST}']", 
               "Setting: Test Setup | [u'My Test Setup']", 
               "Setting: Test Teardown | [u'My Test Teardown']", 
               "Setting: Test Timeout | [u'10 seconds', u'No tarrying allowed']", 
               "Setting: Meta: My Meta | [u'data']", 
               "Setting: Library | [u'OperatingSystem']",
               "Setting: Library | [u'TestLib']",
               "Setting: Resource | [u'resources/resource.html']",
               "Setting: Resource | [u'PathResource.html']",
               "Setting: Resource | [u'spec_resource.html']",
               'End Settings', 
               'Start Variables', 
               "Variable: ${SCALAR} | [u'value']", 
               "Variable: @{LIST} | [u'1', u'2', u'3', u'4', u'a', u'b', u'c', u'd']", 
               'End Variables', 
               'Start Test Cases', 
               'Start Test: My Test', 
               "Setting: Documentation | [u'This is _test_ *case* documentation']", 
               "Setting: Setup | [u'My Overriding Test Setup']", 
               "Setting: Tags | [u'test 1']", 
               "Setting: Timeout | [u'2 seconds', u\"I'm in a great hurry\"]", 
               'KW: Log', 
               "Setting: Teardown | [u'My Overriding Test Teardown']", 
               'End Test', 
               'End Test Cases', 
               'Start User Keywords', 
               'Start UK: My Test Setup', 
               'End UK', 
               'Start UK: My Suite Teardown',
               "Setting: Arguments | [u'${scalar arg}', u'@{list arg}']", 
               "Setting: Documentation | [u'This is *user* _keyword_ documentation']", 
               'Setting: Timeout | [u\'1 second\', u"I\'m faster than you"]', 
               'KW: Log', 
               'KW: Log Many', 
               "Setting: Return | [u'Success']", 
               'End UK', 
               'End User Keywords']
        for act, expected in zip(serializer.record, exp):
            assert_equals(act, expected)
    
             
if __name__  == '__main__':
    unittest.main()
