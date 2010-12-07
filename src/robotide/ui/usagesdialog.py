import wx

from robotide.widgets import Dialog, List, VerticalSizer


class UsagesDialog(Dialog):

    def __init__(self, name, usages):
        self._selection_listeners = []
        self.usages = list(usages)
        usage_labels = [[u.usage, u.datafile.name] for u in self.usages]
        Dialog.__init__(self, "'%s' - %d usages"
                                    % (name, len(usage_labels)))
        self.SetSizer(VerticalSizer())
        usage_list = List(self, ['Usage', 'Source'], usage_labels)
        usage_list.add_selection_listener(self._usage_selected)
        self.Sizer.add_expanding(usage_list)

    def _usage_selected(self, idx):
        for listener in self._selection_listeners:
            listener(self.usages[idx].item.parent)

    def add_selection_listener(self, listener):
        self._selection_listeners.append(listener)