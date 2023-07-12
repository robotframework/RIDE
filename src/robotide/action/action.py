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


def action_factory(action_info):
    if action_info.is_separator():
        return _MenuSeparator(action_info)
    return Action(action_info)


class _Registrable(object):

    def __init__(self, action_info):
        self._registered_to = []
        self.action = None
        self.shortcut = None
        self.icon = None
        self._insertion_point = action_info.insertion_point
        self._enabled = True
        self._enabled_status_listeners = []

    disable = enable = lambda event: None

    def is_separator(self):
        return False

    def get_insertion_index(self, menu):
        return self._insertion_point.get_index(menu)

    def register(self, registerer):
        self._registered_to.append(registerer)

    def unregister(self):
        for registerer in self._registered_to:
            registerer.unregister(self)
        self._registered_to = []

    def has_action(self):
        return self.action is not None

    def has_shortcut(self):
        return bool(self.shortcut)

    def has_icon(self):
        return self.icon is not None

    def inform_changes_in_enabled_status(self, listener):
        self._enabled_status_listeners.append(listener)


class Action(_Registrable):
    """Acts based on user actions if action is enabled. Created from `ActionInfo`.

    If `ActionInfo` contains container, acts and allows to select related UI
    widgets (menu item, toolbar button) and shortcuts only if the focus is in the given 
    container or its children.
    Action can be set enabled or disabled which enables/disables also related UI
    widgets and shortcut.
    """

    def __init__(self, action_info):
        _Registrable.__init__(self, action_info)
        self.menu_name = action_info.menu_name
        self.name = action_info.name
        self.action = action_info.action
        self.container = action_info.container
        self.shortcut = action_info.shortcut
        self.icon = action_info.icon
        self.doc = action_info.doc
        # print("DEBUG: Action: %s::%s" % (self.menu_name,self.name))

    def get_shortcut(self):
        return self.shortcut.printable

    def act(self, event):
        if self.is_active():
            self.action(event)

    def disable(self):
        """Disables action and related menu item, toolbar button and shortcut"""
        self._enabled = False
        self._inform_changes_in_enabled_status()

    def enable(self):
        """Enables action and related menu item, toolbar button and shortcut"""
        self._enabled = True
        self._inform_changes_in_enabled_status()

    def _inform_changes_in_enabled_status(self):
        for listener in self._enabled_status_listeners:
            listener.enabled_status_changed(self)

    def is_active(self):
        if self._is_always_inactive() or not self._enabled:
            return False
        if self._is_always_active():
            return True
        return self._container_is_active()

    def _is_always_inactive(self):
        return self.action is None

    def _is_always_active(self):
        return self.container is None

    def _container_is_active(self):
        if not self.container.IsShownOnScreen():
            return False
        widget = self.container.FindFocus()
        while widget:
            if widget == self.container.Parent:
                return True
            widget = widget.GetParent()
        return False


class _MenuSeparator(_Registrable):

    def __init__(self, action_info):
        _Registrable.__init__(self, action_info)
        self.menu_name = action_info.menu_name
        self.name = '---'

    def is_separator(self):
        return True
