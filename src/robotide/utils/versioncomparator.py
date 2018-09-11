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

from pkg_resources import parse_version


def cmp_versions(version1, version2):
    if version1 is None:
        if version2 is None:
            return 0
        else:
            return -1
    if version2 is None:
        return 1
    if parse_version(version1) == parse_version(version2):
        return 0
    elif parse_version(version1) > parse_version(version2):
        return 1
    return -1
