# Copyright 2010 Orbitz WorldWide
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Modified by NSN
#  Copyright 2010-2012 Nokia Solutions and Networks
#  Copyright 2013-2015 Nokia Networks
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

import codecs
import os

from robotide.context import IS_WINDOWS
from sys import getfilesystemencoding

OUTPUT_ENCODING = getfilesystemencoding()


def _write_windows(fh, lines):
    for item in lines:
        if isinstance(item, str):
            enc_arg = item.encode('UTF-8')  # OUTPUT_ENCODING
        else:
            enc_arg = item
        try:
            fh.write(enc_arg)
            fh.write("\n".encode(OUTPUT_ENCODING))
        except UnicodeError:
            fh.write(bytes(item, 'UTF-8'))
            fh.write(b"\n")


def _write_linux(fh, lines):
    for item in lines:
        if isinstance(item, str):
            fh.write(item)
            fh.write("\n")
        else:
            try:
                fh.write(item.decode('UTF-8'))
                fh.write("\n")
            except (UnicodeError, TypeError) as e:
                print(f"FileWriter: unexpected UnicodeError or TypeError at position: {fh.tell()}")
                raise e


class FileWriter:

    @staticmethod
    def write(file_path, lines, windows_mode, mode='w'):
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        if IS_WINDOWS:
            f = codecs.open(file_path, mode=windows_mode)
            _write_windows(f, lines)
        else:
            f = codecs.open(file_path, mode, "UTF-8")
            # DEBUG: f.write("\n".join(lines))
            _write_linux(f, lines)
        f.close()
