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

import os
import sys
from robot.errors import DataError
from robotide import utils
from iteminfo import _XMLKeywordContent
from robotide.preferences.settings import SETTINGS_DIRECTORY

LIBRARY_XML_DIRECTORY = os.path.join(SETTINGS_DIRECTORY, 'library_xmls')
if not os.path.isdir(LIBRARY_XML_DIRECTORY):
    os.makedirs(LIBRARY_XML_DIRECTORY)

def init_from_spec(name):
    specfile = _find_from_library_xml_directory(name + '.xml') or utils.find_from_pythonpath(name + '.xml')
    return _init_from_specfile(specfile, name)

def _find_from_library_xml_directory(name):
    path = os.path.join(LIBRARY_XML_DIRECTORY, name)
    return path if os.path.isfile(path) else None

def _init_from_specfile(specfile, name):
    if not specfile:
        return []
    try:
        return _parse_xml(specfile, name)
    except Exception:
        # TODO: which exception to catch?
        return []

def _parse_xml(file, name):
    root = utils.ET.parse(file).getroot()
    if root.tag != 'keywordspec':
        # TODO: XML validation errors should be logged
        return [], ''
    kw_nodes = root.findall('keywords/kw') + root.findall('kw')
    source_type = root.get('type')
    if source_type == 'resource':
        source_type += ' file'
    return [_XMLKeywordContent(node, name, source_type) for node in kw_nodes]

def get_path(name, basedir):
    if not _is_library_by_path(name):
        return name.replace(' ', '')
    return _resolve_path(name.replace('/', os.sep), basedir)

def _is_library_by_path(path):
    return path.lower().endswith(('.py', '.java', '.class', '/', os.sep))

def _resolve_path(path, basedir):
    for base in [basedir] + sys.path:
        if not (base and os.path.isdir(base)):
            continue
        ret = os.path.join(base, path)
        if os.path.isfile(ret):
            return ret
        if os.path.isdir(ret) and os.path.isfile(os.path.join(ret, '__init__.py')):
            return ret
    raise DataError

def _get_library_name(name):
    if os.path.exists(name):
        return name
    return name.replace(' ', '')

def get_name_from_xml(path):
    try:
        root = utils.ET.parse(path).getroot()
        name = root.get('name')
        return name
    except:
        return None