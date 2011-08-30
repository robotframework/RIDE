#  Copyright 2008-2011 Nokia Siemens Networks Oyj
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

from robotide.robotapi import TestLibrary as RobotTestLibrary
from robotide.errors import DataError
from robotide.publish import RideLogException
from robotide import utils

from iteminfo import LibraryKeywordInfo, _XMLKeywordContent


class Spec(object):

    def _init_from_specfile(self, specfile):
        try:
            return self._parse_xml(specfile)
        except:
            # TODO: which exception to catch?
            return [], ''

    def _parse_xml(self, file):
        root = utils.DomWrapper(file)
        if root.name != 'keywordspec':
            # TODO: XML validation errors should be logged
            return [], ''
        kw_nodes = root.get_nodes('keywords/kw') + root.get_nodes('kw')
        source_type = root.attrs['type']
        if source_type == 'resource':
            source_type += ' file'
        keywords = [ _XMLKeywordContent(node, self.name, source_type)
                     for node in kw_nodes ]
        return keywords, root.doc


class LibrarySpec(Spec):

    _alias = None
    keywords = tuple()

    def __init__(self, name, args=None):
        self.name = self._get_library_name(name)
        if args and len(args) >= 2 and isinstance(args[-2], basestring) and args[-2].upper() == 'WITH NAME':
            self._alias = args[-1]
            args = args[:-2]
        try:
            self.keywords, self.doc = self._init_from_library(self.name, args)
        except (ImportError, DataError), err:
            specfile = utils.find_from_pythonpath(self.name + '.xml')
            self.keywords, self.doc = self._init_from_specfile(specfile)
            if not self.keywords:
                msg = 'Importing test library "%s" failed' % self.name
                RideLogException(message=msg, exception=err, level='WARN').publish()

    def _init_from_library(self, name, args):
        lib = RobotTestLibrary(name, args)
        keywords = [LibraryKeywordInfo(kw).with_alias(self._alias) for kw in lib.handlers.values()]
        return keywords, lib.doc

    def _get_library_name(self, name):
        if self._alias:
            return self._alias
        if os.path.exists(name):
            return name
        return name.replace(' ', '')
