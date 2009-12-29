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

from wx import grid

from robotide.utils import PopupMenu
from clipboard import ClipboardHandler


class GridEditor(grid.Grid):

    def __init__(self, parent):
        grid.Grid.__init__(self, parent)
        self._bind_to_events()
        self._edit_history = []
        self.active_coords = _GridCoordinates()
        self._clipboard_handler = ClipboardHandler(self)
        self.SelectBlock(0,0,0,0)

    def _bind_to_events(self):
        self.Bind(grid.EVT_GRID_SELECT_CELL, self.OnSelectCell)
        self.Bind(grid.EVT_GRID_RANGE_SELECT, self.OnRangeSelect)
        self.Bind(grid.EVT_GRID_CELL_RIGHT_CLICK, self.OnCellRightClick)

    def OnSelectCell(self, event):
        self.active_coords.set_from_single_selection(event)
        self.AutoSizeRows()
        event.Skip()

    def OnRangeSelect(self, event):
        if event.Selecting():
            self.active_coords.set_from_range_selection(self, event)

    def OnCellRightClick(self, event):
        PopupMenu(self, ['Cut\tCtrl-X', 'Copy\tCtrl-C', 'Paste\tCtrl-V', '---',
                         'Delete\tDel'])

    def copy(self):
        self._clipboard_handler.copy()

    def cut(self):
        self._clipboard_handler.cut()
        self._clear_selected_cells()

    def _clear_selected_cells(self):
        for row, col in self.active_coords.get_selected_cells():
            self.write_cell(row, col, '')

    def get_selected_content(self):
        data = []
        for row in self.active_coords.get_selected_rows():
            data.append([self.GetCellValue(row, col) for
                         col in self.active_coords.get_selected_cols()])
        return data

    def delete(self, event=None):
        if self.IsCellEditControlShown():
            # This is needed in Windows
            editor = self.get_cell_edit_control()
            start, end = editor.GetSelection()
            if start == end:
                end += 1
            editor.Remove(start, end)
            # TODO: is this really needed??
            if event:
                event.Skip()
        else:
            self._clear_selected_cells()

    def paste(self):
        self._clipboard_handler.paste()

    def get_cell_edit_control(self):
        return self.GetCellEditor(*self.active_coords.cell).GetControl()

    def write_cell(self, row, col, value):
        self.SetCellValue(row, col, value)

    def undo(self):
        if self._edit_history:
            self.ClearGrid()
            self._write_data(self._edit_history.pop())
            self._save_keywords(append_to_history=False)


class _GridCoordinates(object):
    cell = property(lambda self: (self.topleft.row, self.topleft.col))

    def __init__(self):
        self._set((0,0))

    def _set(self, topleft, bottomright=None):
        cell = _Cell(topleft[0], topleft[1])
        self.topleft = cell
        self.bottomright = bottomright and \
                _Cell(bottomright[0], bottomright[1]) or cell

    def set_from_single_selection(self, event):
        self._set((event.Row, event.Col))

    def set_from_range_selection(self, grid, event):
        self._set(*self._get_bounding_coordinates(grid, event))

    def _get_bounding_coordinates(self, grid, event):
        whole_row_selection = grid.SelectedRows
        if whole_row_selection:
            return (whole_row_selection[0], 0),\
                   (whole_row_selection[-1], grid.NumberCols-1)
        return (event.TopLeftCoords.Row,event.TopLeftCoords.Col),\
               (event.BottomRightCoords.Row, event.BottomRightCoords.Col)

    def get_selected_rows(self):
        """Returns a list containing indices of rows currently selected."""
        return range(self.topleft.row, self.bottomright.row+1)

    def get_selected_cols(self):
        """Returns a list containing indices of columns currently selected."""
        return range(self.topleft.col, self.bottomright.col+1)

    def get_selected_cells(self):
        """Return selected cells as a list of tuples (row, column)."""
        return [(row, col) for col in self.get_selected_cols()
                           for row in self.get_selected_rows()]


class _Cell(object):

    def __init__(self, row, col):
        self.row = row
        self.col = col
