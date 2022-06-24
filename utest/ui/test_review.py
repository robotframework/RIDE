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
from utest.resources import datafilereader
from robotide.ui.review import ReviewRunner
from robotide.publish import PUBLISHER


class TestReview(unittest.TestCase):

    def setUp(self):
        self.project = datafilereader.construct_project(
            datafilereader.UNUSED_KEYWORDS_PATH)
        self.runner = ReviewRunner(self.project, self)

    def tearDown(self):
        self.project.close()
        PUBLISHER.unsubscribe_all()

    def test_filter(self):
        assert self.helper(
            True, False, False, False, False, "",
            ["Test suite 1", "Test suite 2", "Res1", "Abc", "Foobar"])
        assert self.helper(
            True, False, False, False, True, "",
            ["Test suite 1", "Test suite 2"])
        assert self.helper(
            False, True, False, False, True, "", ["Res1", "Abc", "Foobar"])
        assert self.helper(True, True, False, False, True,
                                "1", ["Test suite 1", "Res1"])
        assert self.helper(True, True, True, False, True,
                                "1,2", ["Abc", "Foobar"])
        assert self.helper(True, True, True, True, True,
                                "^.es.*1$", ["Test suite 2", "Abc", "Foobar"])
        assert self.helper(
            True, True, False, True, True, ",,",
            ["Test suite 1", "Test suite 2", "Res1", "Abc", "Foobar"])
        assert self.helper(
            True, True, False, False, True, ",s,",
            ["Test suite 1", "Test suite 2", "Res1"])
        assert self.helper(True, True, True, True, True,
                                ".*es,.*o{2}", ["Abc"])

    def helper(self, tcfiles, resfiles, exclude, regex, active, string,
               results):
        self.runner.set_filter_active(active)
        self.runner.set_filter_mode(exclude)
        self.runner.set_filter_source_testcases(tcfiles)
        self.runner.set_filter_source_resources(resfiles)
        self.runner.set_filter_use_regex(regex)
        self.runner.parse_filter_string(string)

        counter = 0
        for df in self.runner._get_datafile_list():
            if df.name not in results:
                print("\"%s\" should have been filtered out " % df.name)
                return False
            counter += 1

        all_items_checked = counter == len(results)
        if not all_items_checked:
            print("Result contained %d files, expected %d" % \
                (counter, len(results)))
        return all_items_checked


if __name__ == "__main__":
    unittest.main()
