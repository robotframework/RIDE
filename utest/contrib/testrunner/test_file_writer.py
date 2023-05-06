#  Copyright 2023-     Robot Framework Foundation
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
import tempfile
import unittest

from robotide.contrib.testrunner.FileWriter import FileWriter


class FileWriterTests(unittest.TestCase):

    def test_file_writer(self):
        tmp_dir = tempfile.mkdtemp()
        temp_file = tempfile.mkstemp(dir=tmp_dir)
        temp_file = os.path.join(tmp_dir, temp_file[1])
        args = ['-C', 'off',
                '-W', '7',
                '-P', '/Python Dir:/opt/testlibs',
                '-d', 'C:\\Work\\Test 1',
                '--suite', 'suite_name_1',
                '--test', 'test_1']
        FileWriter.write(temp_file, args, 'wb')
        with open(temp_file, 'r') as file_reader:
            lines = file_reader.readlines()
        try:
            os.remove(temp_file)
        except PermissionError:
            pass
        content = [s.strip() for s in lines]
        self.assertListEqual(content, args)

    def test_file_writer_new_file(self):
        temp_file = "/tmp/a/b/new_file.txt"
        args = ['-C', 'off',
                '-W', '7',
                '-P', '/Python Dir:/opt/testlibs',
                '-d', 'C:\\Work\\Test 1',
                '--suite', 'suite_name_1',
                '--test', 'test_1']
        FileWriter.write(temp_file, args, 'wb')
        with open(temp_file, 'r') as file_reader:
            lines = file_reader.readlines()
        try:
            os.remove(temp_file)
        except PermissionError:
            pass
        content = [s.strip() for s in lines]
        self.assertListEqual(content, args)

    def test_file_writer_bytes(self):
        tmp_dir = tempfile.mkdtemp()
        temp_file = tempfile.mkstemp(dir=tmp_dir)
        temp_file = os.path.join(tmp_dir, temp_file[1])
        args = [b'-C', b'off',
                b'-W', b'7',
                b'-P', b'/Python Dir:/opt/testlibs',
                b'-d', b'C:\\Work\\Test 1',
                b'--suite', b'suite_name_1',
                b'--test', b'test_1']
        FileWriter.write(temp_file, args, 'wb', 'wb')
        with open(temp_file, 'rb') as file_reader:
            lines = file_reader.readlines()
        try:
            os.remove(temp_file)
        except PermissionError:
            pass
        content = [s.strip() for s in lines]
        self.assertListEqual(content, args)


if __name__ == '__main__':
    unittest.main()
