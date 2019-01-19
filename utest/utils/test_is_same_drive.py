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

import os
import unittest
from robotide.context import IS_WINDOWS
from robotide.utils import is_same_drive

if IS_WINDOWS:

    class IsSameDriveTestCase(unittest.TestCase):

        def test_same_drive_is_case_insensitive(self):
            self.assertTrue(is_same_drive('D:', 'd:'))
            self.assertFalse(is_same_drive('x:', 'E:'))

        def test_same_drive_with_different_path(self):
            path1 = os.path.join('x:', 'foo', 'bar.txt')
            path2 = os.path.join('x:', 'zoo')
            not_same_drive = os.path.join('y:', 'bb')
            self.assertTrue(is_same_drive(path1, path2))
            self.assertFalse(is_same_drive(path1, not_same_drive))
            self.assertFalse(is_same_drive(not_same_drive, path1))

        def test_same_drive_with_same_path(self):
            path = os.path.join('a:', 'quu', 'huu.out')
            self.assertTrue(is_same_drive(path, path))

    if __name__ == '__main__':
        unittest.main()


