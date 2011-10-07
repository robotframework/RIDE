#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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

from abstractxmlwriter import AbstractXmlWriter


def XmlWriter(path):
    if path == 'NONE':
        return FakeXMLWriter()
    if os.name == 'java':
        from jyxmlwriter import XmlWriter
    else:
        from pyxmlwriter import XmlWriter
    return XmlWriter(path)


class FakeXMLWriter(AbstractXmlWriter):
    closed = False
    _start = _content = _end = _close = lambda self, *args: None
