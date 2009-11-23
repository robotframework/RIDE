#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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
import os


def find_from_pythonpath(name):
    for dirpath in sys.path:
        if not os.path.isdir(dirpath):
            continue
        path = os.path.join(dirpath, name)
        if os.path.isfile(path):
            return path
    return None


class History(object):

    def __init__(self):
        self._back = []
        self._forward = []

    def change(self, state):
        if not self._back or state != self._back[-1]:
            self._back.append(state)
            self._forward = []

    def back(self):
        if not self._back:
            return None
        if len(self._back) > 1:
            self._forward.append(self._back.pop())
        return self._back[-1]

    def forward(self):
        if not self._forward:
            return None
        state = self._forward.pop()
        self._back.append(state)
        return state
    
    def top(self):
        return self._back and self._back[-1] or None


class RobotDataList(list):

    def __init__(self, datafile, data=[]):
        list.__init__(self)
        self.datafile = datafile
        self._parse_data(data)

    def swap(self, index1, index2):
        self[index1], self[index2] = self[index2], self[index1]
        self.datafile.dirty = True

    def move_up(self, item):
        index = self.index(item)
        if index:
            self.swap(index-1, index)
            self.datafile.dirty = True
            return True
        return False

    def move_down(self, item):
        index = self.index(item)
        if index < len(self)-1:
            self.swap(index, index+1)
            self.datafile.dirty = True
            return True
        return False

    def pop(self, index):
        self.datafile.dirty = True
        list.pop(self, index)
