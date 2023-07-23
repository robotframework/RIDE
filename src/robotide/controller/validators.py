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

from ..publish.messages import RideInputValidationError

ERROR_ILLEGAL_CHARACTERS = "Filename contains illegal characters"
ERROR_EMPTY_FILENAME = "Empty filename"
ERROR_NEWLINES_IN_THE_FILENAME = "Newlines in the filename"
ERROR_FILE_ALREADY_EXISTS = "File %s already exists"


class BaseNameValidator(object):

    def __init__(self, new_basename):
        self._new_basename = new_basename

    def validate(self, context):
        # Try-except is needed to check if file can be created if named like this, using open()
        # http://code.google.com/p/robotframework-ride/issues/detail?id=1111
        import pathlib
        try:
            file_name = '%s.%s' % (self._new_basename, context.get_format())
            file_path = os.path.join(context.directory, file_name)
            if self._file_exists(file_path):
                RideInputValidationError(message=ERROR_FILE_ALREADY_EXISTS % file_path).publish()
                return False
            if '\\n' in self._new_basename or '\n' in self._new_basename:
                RideInputValidationError(message=ERROR_NEWLINES_IN_THE_FILENAME).publish()
                return False
            if len(self._new_basename.strip()) == 0:
                RideInputValidationError(message=ERROR_EMPTY_FILENAME).publish()
                return False
            created_dir = False
            try:
                if pathlib.PurePath(file_path).parent != pathlib.PurePath('.'):
                    #  print("DEBUG: Creating dirs %s", pathlib.PurePath(filePath).parent)
                    pathlib.Path(pathlib.PurePath(file_path).parent).mkdir(parents=False, exist_ok=True)
                    created_dir = True
                #  print("DEBUG: Creating file %s", filePath)
                open(file_path, "w").close()
            finally:
                try:
                    os.remove(file_path)  # If file creation failed, then this will trigger validation error
                    if created_dir:
                        os.rmdir(pathlib.PurePath(file_path).parent)
                except Exception as e:
                    print(e)
            return True
        except (IOError, OSError):
            RideInputValidationError(message=ERROR_ILLEGAL_CHARACTERS).publish()
            return False

    @staticmethod
    def _file_exists(filename):
        return os.path.exists(filename)
