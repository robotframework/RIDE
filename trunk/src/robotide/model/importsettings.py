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

from robotide import context
from robotide import utils

from settings import ResourceImport, LibraryImport, VariablesImport


class ImportSettings(utils.RobotDataList):

    def _parse_data(self, data):
        import_classes = {'Resource': ResourceImport,
                          'Library': LibraryImport,
                          'Variables': VariablesImport}
        for item in data:
            import_class = import_classes[item.name]
            self.append(import_class(item._item.value))

    def new_resource(self, value):
        self._new_import(ResourceImport, [value])
        resource_import_name = self[-1].name
        context.APP.import_new_resource(self.datafile, resource_import_name)

    def new_library(self, value):
        self._new_import(LibraryImport, utils.split_value(value))
    
    def resource_updated(self, index):
        resource_import_name = self[index].name
        context.APP.import_new_resource(self.datafile, resource_import_name)
    
    def new_variables(self, value):
        self._new_import(VariablesImport, utils.split_value(value))

    def _new_import(self, class_, value):
        self.append(class_(value))

    def serialize(self, serializer):
        for item in self:
            item.serialize(serializer)

    def get_resource_imports(self):
        return [ res.name for res in self._get_imports_by_type(ResourceImport) ]

    def get_library_imports(self):
        return self._get_imports_by_type(LibraryImport)

    def get_variable_imports(self):
        return self._get_imports_by_type(VariablesImport)

    def _get_imports_by_type(self, class_):
        return [ item for item in self if isinstance(item, class_) ]
