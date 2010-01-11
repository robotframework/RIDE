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

from datalist import RobotDataList


class Metadata(RobotDataList):

    def _parse_data(self, data):
        for name, value in data.items():
            self.append(MetaItem(self.datafile, name, value))

    def new_metadata(self, name, value):
        self.append(MetaItem(self.datafile, name, value))
        self.datafile.dirty = True

    def serialize(self, serializer):
        for meta in self:
            meta.serialize(serializer)


class MetaItem(object):

    def __init__(self, datafile, name, value=None):
        self.name = name
        self.value = value
        self._datafile = datafile

    def serialize(self, serializer):
        if self.name:
            serializer.setting('Meta: %s' % self.name, [self.value])

    def set_name_and_value(self, name, value):
        self.name, self.value = name, value
        self._datafile.dirty = True
