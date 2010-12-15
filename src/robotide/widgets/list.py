import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin


class List(wx.ListCtrl, ListCtrlAutoWidthMixin):

    def __init__(self, parent, headers, data):
        wx.ListCtrl.__init__(self, parent,
                             style=wx.LC_REPORT|wx.LC_SINGLE_SEL|wx.LC_HRULES)
        ListCtrlAutoWidthMixin.__init__(self)
        self._selection_listeners = []
        self._populate(headers, data)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListItemSelected)

    def _populate(self, headers, data):
        self._create_headers(headers)
        self._populate_list(data)

    def _create_headers(self, headers):
        for idx, name in enumerate(headers):
            self.InsertColumn(idx, name)
        self.SetColumnWidth(0, 200)

    def _populate_list(self, data):
        for rowidx, rowdata in enumerate(data):
            self.InsertStringItem(rowidx, rowdata[0])
            for colidx in range(1, len(rowdata)):
                self.SetStringItem(rowidx, colidx, rowdata[colidx])

    def add_selection_listener(self, listener):
        self._selection_listeners.append(listener)

    def OnListItemSelected(self, event):
        for listener in self._selection_listeners:
            listener(event.Index)
