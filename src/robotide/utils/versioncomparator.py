#  Copyright 2008-2015 Nokia Solutions and Networks
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
import re


def cmp_versions(version1, version2):
    if version1 == version2:
        return 0
    if version1 is None:
        return -1
    if version2 is None:
        return 1
    l1 = _version_string_to_list(version1)
    l2 = _version_string_to_list(version2)
    d = len(l1) - len(l2)
    if d > 0:
        l2 += ['' for _ in range(d)]
    if d < 0:
        l1 += ['' for _ in range(-d)]
    return cmp(l1, l2)

_PREVIEW_VERSION = re.compile(r'(\d+)(\.\d+)*(a|b|rc)(\d*)$')
_PREVIEW_PREFERENCE = {'a':-3, 'b':-2, 'rc':-1}

def _version_string_to_list(version_string):
    if version_string == 'trunk':
        return [-100]
    version_list = version_string.split('.')
    if _PREVIEW_VERSION.match(version_string):
        m = _PREVIEW_VERSION.match(version_list[-1])
        version_list[-1] = m.group(1)
        version_list += [_PREVIEW_PREFERENCE[m.group(3)]]
        version_list += [m.group(4)]
    return _strip_leading_zeros(version_list)

def _strip_leading_zeros(version_list):
    while version_list and version_list[-1] == '0':
        version_list.pop()
    return version_list
