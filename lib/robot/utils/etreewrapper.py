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

import sys
from StringIO import StringIO
try:
    import xml.etree.cElementTree as ET
except ImportError:
    try:
        import cElementTree as ET
    except ImportError:
        try:
            import xml.etree.ElementTree as ET
            # Raises ImportError due to missing expat on IronPython by default
            ET.parse(StringIO('<test/>'))
        except ImportError:
            try:
                import elementtree.ElementTree as ET
            except ImportError:
                raise ImportError('No valid ElementTree XML parser module found')


def get_root(path=None, string=None, node=None):
    # This should NOT be changed to 'if not node:'. See chapter Truth Testing
    # from http://effbot.org/zone/element.htm#the-element-type
    if node is not None:
        return node
    source = _get_source(path, string)
    try:
        return ET.parse(source).getroot()
    finally:
        if hasattr(source, 'close'):
            source.close()

def _get_source(path, string):
    if not path:
        return StringIO(string)
    # ElementTree 1.2.7 preview (first ET with IronPython support) doesn't
    # handler non-ASCII chars correctly if an open file given to it.
    if sys.platform == 'cli':
        return path
    # ET.parse doesn't close files it opens, which causes serious problems
    # with Jython 2.5(.1) on Windows: http://bugs.jython.org/issue1598
    return open(path, 'rb')
