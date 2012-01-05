#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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

from robotide.robotapi import is_var
from robotide.utils import find_variable_basenames, is_scalar_variable


def parse_arguments_to_var_dict(args, name):
    result = {}
    for arg in args:
        parsed = parse_argument(arg)
        if parsed:
            result[parsed[0]] = parsed[1]
    if not args and name:
        for var in find_variable_basenames(name):
            if is_scalar_variable(var):
                result[var] = None
    return result

default_val_regexp = re.compile(r'([$@]\{.*\})\s*=\s*(.*)')

def parse_argument(argument):
    match = default_val_regexp.match(argument)
    if match:
        return (match.group(1), match.group(2))
    if is_var(argument):
        return (argument, None)
    return None