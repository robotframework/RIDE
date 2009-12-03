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


"""Module for handling UI actions.

Menu entries, keyboard shortcuts and toolbar buttons (UI action) are created 
using `ActionInfo` class in RIDE. This class is instantiated with proper data 
and registered to RIDE using register_action method from `Plugin` class.
Registering mechanism allows multiple actions to be registered to the same
UI action. In case UI action does not exist, it is created. Menu separators are
created by instantiating and registering `SeparatorInfo`.

UI action triggers action if the related UI container's child component has
focus. In case action does not have container, it is always called.

For creating multiple actions there is convenience method `ActionInfoCollection`
which generates `ActionInfo` objects from given multiline string.
"""


from actioninfo import ActionInfoCollection, SeparatorInfo, ActionInfo
from action import Action