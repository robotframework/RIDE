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

import os

from robotide.robotapi import TestLibrary as RobotTestLibrary
from robotide.errors import DataError
from robotide.publish import RideLogMessage
from robotide import utils

from iteminfo import LibraryKeywordInfo, _XMLKeywordContent


def XMLResource(resource_name):
    specfile = utils.find_from_pythonpath(os.path.splitext(resource_name)[0] + '.xml')
    if specfile:
        return _XMLResource(resource_name, specfile)
    return None


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

    def __init__(self, name, args=None):
        self.name = self._get_library_name(name)
        if args and len(args) >= 2 and args[-2].upper() == 'WITH NAME':
            args = args[:-2]
        try:
            self.keywords, self.doc = self._init_from_library(self.name, args)
        except (ImportError, DataError), err:
            specfile = utils.find_from_pythonpath(self.name + '.xml')
            self.keywords, self.doc = self._init_from_specfile(specfile)
            if not self.keywords:
                msg = 'Importing test library "%s" failed: %s' %\
                      (self.name, err)
                RideLogMessage(message=msg, level='WARN').publish()

    def _init_from_library(self, name, args):
        lib = RobotTestLibrary(name, args)
        keywords = [LibraryKeywordInfo(kw) for kw in lib.handlers.values()]
        return keywords, lib.doc

    def _get_library_name(self, name):
        if os.path.exists(name):
            return name
        return name.replace(' ', '')


class _XMLResource(Spec):
    type = 'resource'
    variables = property(lambda self: self)
    imports = property(lambda self: self)
    get_library_keywords = lambda self: []

    def __init__(self, name, specfile):
        self.source = name
        self.name = utils.printable_name_from_path(name)
        self.keywords, self.doc = self._init_from_specfile(specfile)
        self.resources = []
        self.suites = []
        self.dirty = False

    def get_keywords(self, library_keywords=True):
        return self.keywords

    def get_user_keywords(self):
        return []

    def get_variables(self):
        return []

    def get_resources(self):
        return []

    def replace_scalar(self, value):
        return value

    def replace_variables(self, value):
        return value

    def serialize(self):
        pass

