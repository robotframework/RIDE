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

from ..controller.ctrlcommands import FindOccurrences, FindVariableOccurrences, _Command


class FindUsages(FindOccurrences):

    def execute(self, context):
        from ..controller.macrocontrollers import KeywordNameController
        # print(f"DEBUG: usages/commands.py FindUsages execute context={context}")
        prev = None
        for occ in FindOccurrences.execute(self, context):
            # if hasattr(occ, 'item'):
            #     print(f"DEBUG: usages/commands.py FindUsages execute in loop occ={occ.item}")
            # else:
            #     print(f"DEBUG: usages/commands.py FindUsages execute in loop NOT occ.item occ={occ}")
            #     continue
            if hasattr(occ, 'item') and isinstance(occ.item, KeywordNameController):
                continue
            if prev == occ:
                prev.count += 1
            else:
                if prev:
                    yield prev
                prev = occ
        if prev:
            yield prev


class FindVariableUsages(FindVariableOccurrences):
    
    def execute(self, context):
        prev = None
        for occ in FindVariableOccurrences.execute(self, context):
            if prev == occ:
                prev.count += 1
            else:
                if prev:
                    yield prev
                prev = occ
        if prev:
            yield prev


class FindResourceUsages(_Command):

    def execute(self, context):
        """from ..controller.filecontrollers import TestCaseFileController
        if isinstance(context, TestCaseFileController):
            return"""
        for imp in context.get_where_used():
            yield ResourceUsage(context, imp)


class FindTestFolderUsages(_Command):

    def execute(self, context):
        for imp in context.get_where_used():
            yield ResourceUsage(*imp)


class ResourceUsage(object):

    def __init__(self, resource, imp):
        self.res_name = resource.name
        self.res_src = resource.source
        user = imp.datafile_controller
        self.location = user.filename
        self.name = user.display_name
        self.item = user.imports
        self.parent = user
        self.can_be_renamed = imp.contains_filename(os.path.basename(resource.filename))
