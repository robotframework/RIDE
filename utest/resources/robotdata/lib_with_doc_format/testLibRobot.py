#  Copyright 2018-     Robot Framework Foundation
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

from robot.api.deco import keyword as keyword

ROBOT_LIBRARY_DOC_FORMAT = 'ROBOT'

"""
_Simple_ *robot* _library_
"""

def robot_doc_keyword1():
    """ 
    = doc_format =
    - robot
    """
    pass


@keyword("pretty robot keyword")
def robot_doc_keyword2(arg1, arg2='default value', *args):
    """robot documentaion
    """
    pass
