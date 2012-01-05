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


from robotide.utils import normalize, get_variable_basename, find_variable_basenames


def highlight_matcher(value, content):
    if not value or not content:
        return False
    selection = normalize(value, ignore=['_'])
    if not selection:
        return False
    target = normalize(content, ignore=['_'])
    if not target:
        return False
    if selection == target:
        return True
    return _variable_matches(selection, target)

def _variable_matches(selection, target):
    variable = get_variable_basename(selection)
    if not variable:
        return False
    variables = find_variable_basenames(target)
    if variable in variables:
        return True
    return _list_variable_used_as_scalar(variable, variables)

def _list_variable_used_as_scalar(variable, variables):
    return '$%s' % variable[1:] in variables
