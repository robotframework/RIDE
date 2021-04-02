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

import re

from ..robotapi import is_dict_var, is_list_var, is_scalar_var
from ..utils import variablematcher

default_val_regexp = re.compile(r'([$]\{.*\})\s*=\s*(.*)')


def parse_arguments_to_var_dict(args, name):
    result = {}
    for arg in args:
        name, value = parse_argument(arg)
        if name:
            result[name] = value
    if not args and name:
        for var in variablematcher.find_variable_basenames(name):
            if variablematcher.is_scalar_variable(var):
                result[var] = None
    return result


def parse_argument(argument):
    match = default_val_regexp.match(argument)
    if match:
        return (match.group(1), match.group(2))
    elif is_scalar_var(argument):
        return argument, ''
    elif is_list_var(argument):
        return argument, []
    elif is_dict_var(argument):
        return argument, {}
    else:
        return None, None
