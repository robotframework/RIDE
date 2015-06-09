from robotide.editor import grid


class VariableTableEditor(grid.GridEditor):

    def __init__(self, parent, tree, variables):
        super(VariableTableEditor, self).__init__(parent, 5, 5)
        self.SetRowLabelSize(0)
        #self.SetDefaultColSize(175)
        for row, var in enumerate(variables):
            self.write_cell(row, 0, var.name)
            for cell, v in enumerate(var.value):
                self.write_cell(row, cell + 1, v)
        #self.AutoSizeRows()

    def close(self):
        pass
