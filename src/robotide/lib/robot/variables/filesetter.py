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
#
# This file contains code taken from RobotFramework 7.1

import inspect
import io
import json
try:
    import yaml
except ImportError:
    yaml = None

from robotide.lib.robot.errors import DataError
from robotide.lib.robot.output import LOGGER
from robotide.lib.robot.utils import (DotDict, get_error_message, Importer, is_dict_like,
                                      is_list_like, type_name,)


def dot_dict(value):
    if is_dict_like(value):
        return DotDict((k, dot_dict(v)) for k, v in value.items())
    if is_list_like(value):
        return [dot_dict(v) for v in value]
    return value

def make_var(name, value):
    var_value = dot_dict(value)
    if is_dict_like(var_value):
        symbol = '&'
    elif  is_list_like(var_value):
        symbol = '@'
    else:
        symbol = '$'
    var_name = f"{symbol}" + "{" + name + "}"
    return var_name, var_value


class VariableFileSetter(object):

    def __init__(self, store):
        self._store = store

    def set(self, path_or_variables, args=None, overwrite=False):
        variables = self._import_if_needed(path_or_variables, args)
        self._set(variables, overwrite)
        return variables

    @staticmethod
    def _import_if_needed(path_or_variables, args=None):
        if not isinstance(path_or_variables, str):
            return path_or_variables
        LOGGER.info(f"Importing variable file '{path_or_variables}' with args {args}.")
        if path_or_variables.lower().endswith(('.yaml', '.yml')):
            importer = YamlImporter()
        elif path_or_variables.lower().endswith('.json'):
            importer = JsonImporter()
        else:
            importer = PythonImporter()
        try:
            var_result = importer.import_variables(path_or_variables, args)
            return var_result
        except Exception:
            args = f'with arguments {args} ' if args else ''
            raise DataError(f"Processing variable file '{path_or_variables}' "
                            f"{args}failed: {get_error_message()}")

    def _set(self, variables, overwrite=False):
        for name, value in variables:
            self._store.add(name, value, overwrite)


class PythonImporter:

    def import_variables(self, path, args=None):
        importer = Importer('variable file').import_class_or_module_by_path
        var_file = importer(path, instantiate_with_args=())
        return self._get_variables(var_file, args)

    def _get_variables(self, var_file, args):
        get_variables = (getattr(var_file, 'get_variables', None) or
                         getattr(var_file, 'getVariables', None))
        if get_variables:
            variables = self._get_dynamic(get_variables, args)
        elif not args:
            variables = self._get_static(var_file)
        else:
            raise DataError('Static variable files do not accept arguments.')
        decorated = self._decorate_and_validate(variables)
        return decorated

    def _get_dynamic(self, get_variables, args):
        positional, named = self._resolve_arguments(get_variables, args)
        variables = get_variables(*positional, **dict(named))
        if is_dict_like(variables):
            return variables.items()
        raise DataError(f"Expected '{get_variables.__name__}' to return "
                        f"a dictionary-like value, got {type_name(variables)}.")

    @staticmethod
    def _resolve_arguments(get_variables, args):
        # Avoid cyclic import. Yuck.
        from robot.running.arguments import PythonArgumentParser
        spec = PythonArgumentParser('variable file').parse(get_variables)
        return spec.resolve(args)

    @staticmethod
    def _get_static(var_file):
        names = [attr for attr in dir(var_file) if not attr.startswith('_')]
        if hasattr(var_file, '__all__'):
            names = [name for name in names if name in var_file.__all__]
        variables = [(name, getattr(var_file, name)) for name in names]
        if not inspect.ismodule(var_file):
            variables = [(n, v) for n, v in variables if not callable(v)]
        return variables

    def _decorate_and_validate(self, variables):
        for name, value in variables:
            name = self._decorate(name)
            if name[0] == '@':
                if not is_list_like(value):
                    raise DataError(f"Invalid variable '{name}': Expected a "
                                    f"list-like value, got {type_name(value)}.")
                value = list(value)
            elif name[0] == '&':
                if not is_dict_like(value):
                    raise DataError(f"Invalid variable '{name}': Expected a "
                                    f"dictionary-like value, got {type_name(value)}.")
                value = DotDict(value)
            yield name, value

    @staticmethod
    def _decorate(name):
        if name.startswith('LIST__'):
            return '@{%s}' % name[6:]
        if name.startswith('DICT__'):
            return '&{%s}' % name[6:]
        return '${%s}' % name


class JsonImporter:

    def import_variables(self, path, args=None):
        if args:
            raise DataError('JSON variable files do not accept arguments.')
        variables = self._import(path)
        return [make_var(name, value) for name, value in variables]

    @staticmethod
    def _import(path):
        with io.open(path, encoding='UTF-8') as stream:
            variables = json.load(stream)
        if not is_dict_like(variables):
            raise DataError(f'JSON variable file must be a mapping, '
                            f'got {type_name(variables)}.')
        return variables.items()


class YamlImporter:

    def import_variables(self, path, args=None):
        if args:
            raise DataError('YAML variable files do not accept arguments.')
        variables = self._import(path)
        return [make_var(name, value) for name, value in variables]

    def _import(self, path):
        with io.open(path, encoding='UTF-8') as stream:
            variables = self._load_yaml(stream)
        if not is_dict_like(variables):
            raise DataError(f'YAML variable file must be a mapping, '
                            f'got {type_name(variables)}.')
        return variables.items()

    @staticmethod
    def _load_yaml(stream):
        if not yaml:
            raise DataError('Using YAML variable files requires PyYAML module '
                            'to be installed. Typically you can install it '
                            'by running `pip install pyyaml`.')
        return yaml.full_load(stream)
