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
import sys

from .. import context, robotapi, utils
from ..utils.versioncomparator import cmp_versions
from .iteminfo import _XMLKeywordContent


class SpecInitializer(object):

    def __init__(self, directories=None):
        self._directories = directories or []
        self._directories.append(context.LIBRARY_XML_DIRECTORY)

    def init_from_spec(self, name):
        specfile = self._find_from_pythonpath(name) or \
            self._find_from_library_xml_directories(name)
        return self._init_from_specfile(specfile, name)

    def _find_from_library_xml_directories(self, name):
        for directory in self._directories:
            path = self._find_from_library_xml_directory(directory, name)
            if path:
                return path
        return None

    def _find_from_library_xml_directory(self, directory, name):
        current_xml_file = None
        for xml_file in self._list_xml_files_in(directory):
            name_from_xml = get_name_from_xml(xml_file)
            if name_from_xml == name:
                current_xml_file = self._get_newest_xml_file(
                    xml_file, current_xml_file)
        return current_xml_file

    def _get_newest_xml_file(self, xml_file, current_xml_file):
        version1 = self._get_version(xml_file)
        version2 = self._get_version(current_xml_file)
        if cmp_versions(version1, version2) == 1:
            return xml_file
        return current_xml_file

    @staticmethod
    def _get_version(xml_file):
        try:
            return utils.ET.parse(xml_file).getroot().find('version').text
        except Exception as e:
            print(e)
            return None

    @staticmethod
    def _list_xml_files_in(directory):
        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if path.endswith('.xml') and os.path.isfile(path):
                yield path

    def _find_from_pythonpath(self, name):
        return utils.find_from_pythonpath(name + '.xml')

    def _init_from_specfile(self, specfile, name):
        if not specfile:
            return []
        try:
            return _parse_xml(specfile, name)
        except Exception as e:
            # DEBUG: which exception to catch?
            print(e)
            return []


def _parse_xml(file, name):
    root = utils.ET.parse(file).getroot()
    if root.tag != 'keywordspec':
        # DEBUG: XML validation errors should be logged
        return [], ''
    kw_nodes = root.findall('keywords/kw') + root.findall('kw')
    source_type = root.get('type')
    doc_format = root.get('format')
    if source_type == 'resource':
        source_type += ' file'
    return [_XMLKeywordContent(node, name, source_type, doc_format) for node in kw_nodes]


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
        if os.path.isdir(ret) and \
                os.path.isfile(os.path.join(ret, '__init__.py')):
            return ret
    return None
    # DEBUG raise robotapi.DataError


def _get_library_name(name):
    if os.path.exists(name):
        return name
    return name.replace(' ', '')


def get_name_from_xml(path):
    try:
        root = utils.ET.parse(path).getroot()
        name = root.get('name')
        return name
    except Exception as e:
        print(e)
        return None
