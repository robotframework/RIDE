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

from robotide.application import DataModel
from robotide.errors import NoRideError
from robot.utils.asserts import assert_raises_with_msg
from resources import NO_RIDE_PATH, NO_RIDE_RESOURCE_PATH


EXP_ERROR = "Test data file '%s' is not supposed to be edited with RIDE."


class TestNoRide(unittest.TestCase):

    def test_no_ride_in_test_case_file(self):
        assert_raises_with_msg(NoRideError, EXP_ERROR % NO_RIDE_PATH, 
                               DataModel, NO_RIDE_PATH)

    def test_no_ride_in_resource_file(self):
        assert_raises_with_msg(NoRideError, EXP_ERROR % NO_RIDE_RESOURCE_PATH, 
                               DataModel, NO_RIDE_RESOURCE_PATH)


if __name__ == '__main__':
    unittest.main()
