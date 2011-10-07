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


# Need different unic implementations for different Pythons because:
# 1) Importing unicodedata module on Jython takes a very long time, and doesn't
# seem to be necessary as Java probably already handles normalization.
# Furthermore, Jython on Java 1.5 doesn't even have unicodedata.normalize.
# 2) IronPython 2.6 doesn't have unicodedata and probably doesn't need it.
# 3) CPython doesn't automatically normalize Unicode strings.

if sys.platform.startswith('java'):
    from java.lang import Object, Class
    def unic(item, *args):
        # http://bugs.jython.org/issue1564
        if isinstance(item, Object) and not isinstance(item, Class):
            try:
                item = item.toString()  # http://bugs.jython.org/issue1563
            except:
                return _unrepresentable_object(item)
        return _unic(item, *args)

elif sys.platform == 'cli':
    def unic(item, *args):
        return _unic(item, *args)

else:
    from unicodedata import normalize
    def unic(item, *args):
        return normalize('NFC', _unic(item, *args))


def _unic(item, *args):
    # Based on a recipe from http://code.activestate.com/recipes/466341
    try:
        return unicode(item, *args)
    except UnicodeError:
        try:
            ascii_text = str(item).encode('string_escape')
        except:
            return _unrepresentable_object(item)
        else:
            return unicode(ascii_text)
    except:
        return _unrepresentable_object(item)


def safe_repr(item):
    try:
        return unic(repr(item))
    except UnicodeError:
        return repr(unic(item))
    except:
        return _unrepresentable_object(item)


_unrepresentable_msg = u"<Unrepresentable object '%s'. Error: %s>"

def _unrepresentable_object(item):
    from robot.utils.error import get_error_message
    return _unrepresentable_msg % (item.__class__.__name__, get_error_message())
