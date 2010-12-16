import wx
from wx.lib.mixins.listctrl import ListCtrlAutoWidthMixin


class VirtualList(wx.ListCtrl, ListCtrlAutoWidthMixin):
    _style = wx.LC_REPORT|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VIRTUAL

    def __init__(self, parent, headers, model):
        wx.ListCtrl.__init__(self, parent, style=self._style)
        ListCtrlAutoWidthMixin.__init__(self)
        self._model = model
        self._selection_listeners = []
        self._create_headers(headers)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnListItemSelected)
        self.SetItemCount(model.count)
        self.SetImageList(model.images, wx.IMAGE_LIST_SMALL)

    def _create_headers(self, headers):
        for idx, name in enumerate(headers):
            self.InsertColumn(idx, name)
        self.SetColumnWidth(0, 200)

    def add_selection_listener(self, listener):
        self._selection_listeners.append(listener)

    def OnListItemSelected(self, event):
        for listener in self._selection_listeners:
            listener(event.Index)

    def OnGetItemText(self, row, col):
        return self._model.item_text(row, col)

    def OnGetItemImage(self, item):
        return self._model.image(item)
