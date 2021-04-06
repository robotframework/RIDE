# Copyright 2010 Orbitz WorldWide
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Modified by NSN
#  Copyright 2010-2012 Nokia Solutions and Networks
#  Copyright 2013-2015 Nokia Networks
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

from robotide.robotapi import LOG_LEVELS


class ArgsParser:

    @staticmethod
    def get_message_log_level(args, default='INFO'):
        level = ArgsParser._get_arg_value('-L', '--loglevel',
                                          args, default)
        level_list = level.upper().split(':')
        try:
            min_level = LOG_LEVELS[level_list[0]] or LOG_LEVELS[default]
            for i in level_list:
                min_level = LOG_LEVELS[i] if LOG_LEVELS[i] < min_level else min_level
            return min_level
        except KeyError as e:
            raise TypeError(f"Invalid loglevel: {e}")

    @staticmethod
    def get_output_directory(args, default):
        return ArgsParser._get_arg_value('-d', '--outputdir',
                                         args, default)

    @staticmethod
    def _get_arg_value(short_name, full_name, source, default):
        if short_name in source:
            switch = short_name
        elif full_name in source:
            switch = full_name
        else:
            return default
        i = source.index(switch)
        if len(source) == i:
            return default
        return source[i + 1]
