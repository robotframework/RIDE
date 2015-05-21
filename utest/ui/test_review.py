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
import datafilereader
from robot.utils.asserts import assert_true
from robotide.ui.review import ReviewRunner

class TestReview(unittest.TestCase):
    
    def setUp(self):
        self.project = datafilereader.construct_project(datafilereader.UNUSED_KEYWORDS_PATH)
        self.runner = ReviewRunner(self.project, self)

    def tearDown(self):
        self.project.close()
    
    def test_filter(self):
        assert_true(self.helper(True, False, False, False, False,
                                "", ["Test suite 1", "Test suite 2", "Res1", "Abc", "Foobar"]))
        assert_true(self.helper(True, False, False, False, True,
                                "", ["Test suite 1", "Test suite 2"]))
        assert_true(self.helper(False, True, False, False, True,
                                "", ["Res1", "Abc", "Foobar"]))
        assert_true(self.helper(True, True, False, False, True,
                                "1", ["Test suite 1", "Res1"]))
        assert_true(self.helper(True, True, True, False, True,
                                "1,2", ["Abc", "Foobar"]))
        assert_true(self.helper(True, True, True, True, True,
                                "^.es.*1$", ["Test suite 2", "Abc", "Foobar"]))
        assert_true(self.helper(True, True, False, True, True,
                                ",,", ["Test suite 1", "Test suite 2", "Res1", "Abc", "Foobar"]))
        assert_true(self.helper(True, True, False, False, True,
                                ",s,", ["Test suite 1", "Test suite 2", "Res1"]))
        assert_true(self.helper(True, True, True, True, True,
                                ".*es,.*o{2}", ["Abc"]))

    def helper(self, tcfiles, resfiles, exclude, regex, active, string, expected_results):
        self.runner.set_filter_active(active)
        self.runner.set_filter_mode(exclude)
        self.runner.set_filter_source_testcases(tcfiles)
        self.runner.set_filter_source_resources(resfiles)
        self.runner.set_filter_use_regex(regex)
        self.runner.parse_filter_string(string)
        
        counter = 0
        for df in self.runner._get_datafile_list():
            if df.name not in expected_results:
                print "\"%s\" should have been filtered out " % df.name
                return False
            counter += 1
        
        all_items_checked = counter == len(expected_results)
        if not all_items_checked:
            print "Result contained %d files, expected %d" % (counter, len(expected_results))
        return all_items_checked


if __name__ == "__main__":
    unittest.main()
