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

from robotide.publish import RideImportSettingAdded, RideImportSettingChanged
from robotide import context
from robotide import utils

from datalist import RobotDataList
from settings import ResourceImport, LibraryImport, VariablesImport


class ImportSettings(RobotDataList):

    def pop(self, index):
        self.datafile.set_dirty()
        list.pop(self, index)
        self.datafile.refresh_namespace()

    def _parse_data(self, data):
        import_classes = {'Resource': ResourceImport,
                          'Library': LibraryImport,
                          'Variables': VariablesImport}
        for item in data:
            import_class = import_classes[item.name]
            # Handle invalid imports with empty values.
            if item._item.value:
                self.append(import_class(self.datafile, item._item.value))

    def get_keywords(self):
        kws = []
        kws.extend(self._keywords_from_lib_imports())
        kws.extend(self._keywords_from_res_imports(lambda res:
                                                   res.get_keywords()))
        return kws

    def _keywords_from_lib_imports(self):
        kws = []
        for lib_import in self.get_library_imports():
            name, args = self._replace_vars_from_lib_import(lib_import)
            kws.extend(self.datafile.namespace.get_library_keywords(name, args))
        return kws

    def _replace_vars_from_lib_import(self, lib_import):
        return (self._replace_variables(lib_import.name),
                [ self._replace_variables(arg) for arg in lib_import.args ])

    def _replace_variables(self, value):
        return self.datafile.replace_variables(value)

    def _keywords_from_res_imports(self, kw_harvester):
        kws = []
        for name in self.get_resource_imports():
            # TODO: why does RESOURCEFILECACHE return None in some cases?
            name = self._replace_variables(name)
            res= self.datafile.namespace.get_resource_file(self.datafile.source,
                                                           name)
            if res:
                kws.extend(kw_harvester(res))
        return kws

    def get_user_keywords(self):
        kws = []
        kws.extend(self._keywords_from_res_imports(lambda res: res.keywords))
        return kws

    def get_library_keywords(self):
        kws = []
        kws.extend(self._keywords_from_lib_imports())
        kw_harvester = lambda res: res.imports.get_library_keywords()
        kws.extend(self._keywords_from_res_imports(kw_harvester))
        return kws

    def get_resources(self):
        return self._keywords_from_res_imports(lambda res: [res])

    def get_variables(self):
        vars = []
        vars.extend(self._keywords_from_res_imports(lambda res:
                                                    res.get_variables()))
        vars.extend(self._get_vars_from_files())
        return vars

    def _get_vars_from_files(self):
        vars = []
        for varfile in self._get_variable_files():
            vars.extend([ (varfile.source, var) for var in varfile.keys() ])
        return vars

    def _get_variable_files(self):
        varfiles = []
        for var_settings in self.get_variable_imports():
            # TODO: There is need for namespace object which could be used for
            # all variable replacing
            vars = self.datafile.variables
            name = vars.replace_scalar(var_settings.name)
            args = vars.replace_list(var_settings.args)
            varfile = self.datafile.namespace.get_varfile(self.datafile.source,
                                                          name, args)
            if varfile:
                varfiles.append(varfile)
        return varfiles

    def new_resource(self, value):
        self._new_import(ResourceImport, [value])
        resource_import_name = self[-1].name
        context.APP.import_new_resource(self.datafile, resource_import_name)
        self._publish_new_import('resource')

    def new_library(self, value):
        self._new_import(LibraryImport, utils.split_value(value))
        self._publish_new_import('library')

    def _publish_new_import(self, type_):
        RideImportSettingAdded(datafile=self.datafile, type=type_,
                               name=self[-1].name).publish()
        self.datafile.refresh_namespace()

    def resource_updated(self, index):
        name = self[index].name
        context.APP.import_new_resource(self.datafile, name)
        RideImportSettingChanged(datafile=self.datafile, type='resource',
                                 name=name).publish()
        self.datafile.refresh_namespace()

    def new_variables(self, value):
        self._new_import(VariablesImport, utils.split_value(value))

    def _new_import(self, class_, value):
        self.append(class_(self.datafile, value))
        self.datafile.set_dirty()

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
