import wx


class MenuBar(object):

    def __init__(self, frame):
        self._mb = wx.MenuBar()
        self._frame = frame
        self._create_default_menus()

    def _create_default_menus(self):
        for name in ['&File', '&Edit', '&Tools', '&Help']:
            self._mb.Append(wx.Menu(), name)

    def register_menu_entry(self, entry):
        menu = self._get_or_create_menu(entry.menu_name)
        entry.insert_to_menu(menu, self._frame)

    def register_menu_entries(self, entries):
        for entry in entries:
            self.register_menu_entry(entry)

    def _get_or_create_menu(self, name):
        position = self._mb.FindMenu(name)
        if position == -1:
            self._mb.Append(wx.Menu(), name)
            position = self._mb.FindMenu(name)
        return self._mb.GetMenu(position)

    def register_to_frame(self, frame):
        frame.SetMenuBar(self._mb)


class MenuEntry(object):
    _actions = {}

    def __init__(self, menu_name, name, action, container=None, shortcut=None,
                 doc=''):
        self.id = wx.NewId()
        self.menu_name = menu_name
        self.name = shortcut and '%s\t%s' % (name, shortcut) or name
        self.doc = doc
        self.action = self._get_action_for(shortcut, action, container)

    def _get_action_for(self, shortcut, action, container):
        action_delegator = self._register_action(shortcut)
        action_delegator.add(action, container)
        return action_delegator

    def _register_action(self, shortcut):
        key = shortcut or (self.menu_name, self.name)
        return self._actions.setdefault(key, ActionDelegator())

    def insert_to_menu(self, menu, frame):
        if self._is_not_in_menu(menu):
            menu.Append(self.id, self.name, self.doc)
            frame.Bind(wx.EVT_MENU, self.action, id=self.id)

    def _is_not_in_menu(self, menu):
        id = menu.FindItem(self.name)
        if id == -1:
            return True
        return menu.FindItemById(id).GetItemLabel() != self.name


class MenuSeparator(object):

    def __init__(self, menu):
        self.menu_name = menu

    def insert_to_menu(self, menu, frame):
        menu.AppendSeparator()


class ActionDelegator(object):

    def __init__(self):
        self._actors = []

    def add(self, action, container):
        self._actors.append(Actor(action, container))

    def __call__(self, event):
        for actor in self._actors:
            actor.act()


class Actor(object):

    def __init__(self, action, container):
        self._action = action
        self._container = container

    def act(self):
        if self._should_act():
            self._action()

    def _should_act(self):
        if self._is_always_active():
            return True
        return self._container_is_active()

    def _is_always_active(self):
        return self._container is None

    def _container_is_active(self):
        if not self._container.IsShownOnScreen():
            return False
        widget = wx.GetActiveWindow()
        while widget:
            if widget == self._container.Parent:
                return True
            widget = widget.GetParent()
        return False
