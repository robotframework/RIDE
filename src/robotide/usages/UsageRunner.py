from robotide.controller.commands import FindUsages
from robotide.usages.usagesdialog import UsagesDialog

class Usages(object):

    def __init__(self, controller, highlight):
        self._name = controller.name
        self._controller = controller
        self._highlight = highlight

    def show(self):
        dlg = UsagesDialog(self._name, self._controller.execute(FindUsages(self._name)))
        dlg.add_selection_listener(self._highlight)
        dlg.Show()