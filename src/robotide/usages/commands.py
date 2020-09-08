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

from ..controller import ctrlcommands
# import FindOccurrences, _Command, FindVariableOccurrences
from ..controller import macrocontrollers
# import KeywordNameController


class FindUsages(ctrlcommands.FindOccurrences):

    def execute(self, context):
        prev = None
        for occ in ctrlcommands.FindOccurrences.execute(self, context):
            if isinstance(occ.item, macrocontrollers.KeywordNameController):
                continue
            if prev == occ:
                prev.count += 1
            else:
                if prev:
                    yield prev
                prev = occ
        if prev:
            yield prev


class FindVariableUsages(ctrlcommands.FindVariableOccurrences):
    
    def execute(self, context):
        prev = None
        for occ in ctrlcommands.FindVariableOccurrences.execute(self, context):
            if prev == occ:
                prev.count += 1
            else:
                if prev:
                    yield prev
                prev = occ
        if prev:
            yield prev


class FindResourceUsages(ctrlcommands._Command):

    def execute(self, context):
        for imp in context.get_where_used():
            yield ResourceUsage(context, imp)


class FindTestFolderUsages(ctrlcommands._Command):

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
