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
from fnmatch import fnmatch


class Excludes(object):

    def __init__(self, directory):
        self._settings_directory = directory
        self._exclude_file_path = os.path.join(self._settings_directory, 'excludes')

    def get_excludes(self, separator='\n'):
        return separator.join(self._get_excludes())

    def _get_excludes(self):
        with self._get_exclude_file('r') as exclude_file:
            if not exclude_file:
                return set()
            return set(exclude_file.read().split())

    def remove_path(self, path):
        path = self._normalize(path)
        excludes = self._get_excludes()
        self.write_excludes(set([e for e in excludes if e != path]))

    def write_excludes(self, excludes):
        excludes = [self._normalize(e) for e in excludes]
        with self._get_exclude_file(read_write='w') as exclude_file:
            for exclude in excludes:
                if not exclude:
                    continue
                exclude_file.write("%s\n" % exclude)
        # print("DEBUG:real excluded self._get_excludes()=%s\n" % self._get_excludes())

    def update_excludes(self, new_excludes):
        excludes = self._get_excludes()
        self.write_excludes(excludes.union(new_excludes))
        # print("DEBUG: Excludes, excluded, union %s, %s, %s\n" % (excludes, new_excludes,
        #                                                         excludes.union(new_excludes)))

    def _get_exclude_file(self, read_write):
        if not os.path.exists(self._exclude_file_path) and read_write.startswith('r'):
            if not os.path.isdir(self._settings_directory):
                os.makedirs(self._settings_directory)
            return open(self._exclude_file_path, 'w+', encoding='utf-8')
        if os.path.isdir(self._exclude_file_path):
            raise NameError('"%s" is a directory, not file' % self._exclude_file_path)
        try:
            return open(self._exclude_file_path, read_write, encoding='utf-8')
        except IOError as e:
            print(e)
            raise e  # DEBUG: TODO FIXME

    def contains(self, path, excludes=None):
        if not path:
            return False
        excludes = excludes or self._get_excludes()
        if len(excludes) < 1:
            return False
        path = self._normalize(path)
        excludes = [self._normalize(e) for e in excludes]
        # print("DEBUG: excludes contains %s path %s\n"
        #      "any: %s\n" % (excludes[0], path, any(self._match(path, e) for e in excludes)) )
        return any(self._match(path, e) for e in excludes)

    @staticmethod
    def _match(path, e):
        return fnmatch(path, e) or path.startswith(e)

    @staticmethod
    def _normalize(path):
        if not (path or path.strip()):
            return None
        path = os.path.normcase(os.path.normpath(path))
        ext = os.path.splitext(path)[1]
        if not ext and not path.endswith(('*', '?', ']')):
            path += os.sep
            if '*' in path or '?' in path or ']' in path:
                path += '*'
        return path
