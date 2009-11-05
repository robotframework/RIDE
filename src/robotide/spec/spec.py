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
from robotide import utils


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
        source_type = root.attr_names['type']
        if source_type == 'resource':
            source_type += ' file'
        keywords = [ _XMLKeywordContent(node, self.name, source_type) for node in kw_nodes ]
        return keywords, root.doc


class LibrarySpec(Spec):

    def __init__(self, name, args=None):
        self.name = name.replace(' ', '')
        if args and len(args) >= 2 and args[-2].upper() == 'WITH NAME':
            args = args[:-2]
        try:
            self.keywords, self.doc = self._init_from_library(self.name, args)
        except:
            # TODO: RF TestLibary does not always raise DataError on failure.
            # Need to probably at least log this failure somehow.
            specfile = utils.find_from_pythonpath(self.name + '.xml')
            self.keywords, self.doc = self._init_from_specfile(specfile)

    def _init_from_library(self, name, args):
        lib = RobotTestLibrary(name, args)
        keywords = [ _LibraryKeywordContent(handler, name) for
                     handler in lib.handlers.values() ]
        return keywords, lib.doc


class _XMLResource(Spec):

    def __init__(self, name, specfile):
        self.source = name
        self.name = utils.printable_name_from_path(name)
        self.keywords, self.doc = self._init_from_specfile(specfile)
        self.resources = []
        self.suites = []
        self.dirty = False

    def get_keywords(self, library_keywords=True):
        return self.keywords

    def get_user_keyword(self, longname):
        return None

    def get_variables(self):
        return []

    def get_resources(self):
        return []

    def replace_variables(self, value):
        return value

    def get_keywords_for_content_assist(self, relative=False, filter=''):
        return self.keywords

    def serialize(self):
        pass


class _KeywordContent(object):

    def __init__(self, item, source, source_type):
        self.name = self._get_name(item)
        self.source = source
        self.longname = "%s.%s" % (source, self.name)
        self.doc = self._get_doc(item)
        self.shortdoc = self.doc and self.doc.splitlines()[0] or ''
        self.args = self._format_args(self._parse_args(item))
        self._source_type = source_type

    def get_details(self):
        doc = utils.html_escape(self.doc, formatting=True)
        return 'Source: %s &lt;%s&gt;<br><br>Arguments: %s<br><br>%s' % \
                (self.source, self._source_type, self.args, doc)

    def _get_name(self, item):
        return item.name

    def _get_doc(self, item):
        return item.doc

    def _format_args(self, args):
        return '[ %s ]' % ' | '.join(args)


class _XMLKeywordContent(_KeywordContent):

    def _get_name(self, node):
        return node.attr_names['name']

    def _get_doc(self, node):
        return node.get_node('doc').text

    def _parse_args(self, node):
        args_node = node.get_node('arguments')
        return [ arg_node.text for arg_node in args_node.get_nodes('arg') ]


class _LibraryKeywordContent(_KeywordContent):

    def __init__(self, item, source):
        _KeywordContent.__init__(self, item, source, 'test library')

    def _parse_args(self, handler):
        args = []
        if handler.args:
            args.extend(list(handler.args))
        if handler.defaults:
            for i, value in enumerate(handler.defaults):
                index = len(handler.args) - len(handler.defaults) + i
                args[index] = args[index] + '=' + str(value)
        if handler.varargs:
            args.append('*%s' % handler.varargs)
        return args


class UserKeywordContent(_KeywordContent):

    def _get_doc(self, uk):
        return uk.doc

    def _parse_args(self, uk):
        return [ self._format_arg(arg) for arg in uk.settings.args.value ]

    def _format_arg(self, arg):
        argstr = ''
        if arg and arg[0] == '@':
            argstr += '*'
        tokens = arg.split('=', 1)
        name = tokens[0]
        def_value = len(tokens) > 1 and tokens[1] or ''
        argstr += name[2:-1] # Strip ${} or @{}
        if def_value:
            argstr += '=%s' % def_value
        return argstr
