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

from robotide.lib.robot.running.arguments.embedded import EmbeddedArgumentParser


class EmbeddedArgsHandler(object):

    def __init__(self, keyword):
        if keyword.arguments:
            # raise TypeError('Cannot have normal arguments')
            print('DEBUG: Found normal arguments in embedded arguments keyword.')
        # print(f'DEBUG: embeddedargs.py EmbeddedArgsHandler keyword={keyword.name} longname={keyword.longname}')
        self.name_regexp, self.embedded_args = EmbeddedArgumentParser().parse(keyword.name)
        if hasattr(keyword, 'longname'):
            self.longname_regexp, _ = EmbeddedArgumentParser().parse(keyword.longname)
        if not self.embedded_args:
            raise TypeError('Must have embedded arguments')
