#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
#  Created by Hélio Guilherme <helioxentric@gmail.com>
#  Copyright 2016-     Robot Framework Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import sys

import wx
import wx.stc as stc
from robotide.editor.pythoneditor import PythonSTC
from wx import Colour

# ---------------------------------------------------------------------------
# This is how you pre-establish a file filter so that the dialog
# only shows the extension(s) you want it to.
wildcard = "All files (*.*)|*.*|"                \
           "JASON file (*.json)|*.json|"        \
           "Python source (*.py)|*.py|"         \
           "Robot Framework (*.robot)|*.robot|" \
           "Robot Framework (*.txt)|*.txt|" \
           "YAML file (*.yaml)|*.yaml"
# ----------------------------------------------------------------------

class SourceCodeEditor(PythonSTC):
    def __init__(self, parent, options, style=wx.BORDER_NONE):
        PythonSTC.__init__(self, parent, -1, options, style=style)
        self.SetUpEditor()

    # Some methods to make it compatible with how the wxTextCtrl is used
    def SetValue(self, value):
        val = self.GetReadOnly()
        self.SetReadOnly(False)
        self.SetText(value)
        self.EmptyUndoBuffer()
        self.SetSavePoint()
        self.SetReadOnly(val)

    def SetEditable(self, val):
        self.SetReadOnly(not val)

    def IsModified(self):
        return self.GetModify()

    def Clear(self):
        self.ClearAll()

    def SetInsertionPoint(self, pos):
        self.SetCurrentPos(pos)
        self.SetAnchor(pos)

    def ShowPosition(self, pos):
        line = self.LineFromPosition(pos)
        # self.EnsureVisible(line)
        self.GotoLine(line)

    def GetLastPosition(self):
        return self.GetLength()

    def GetPositionFromLine(self, line):
        return self.PositionFromLine(line)

    def GetRange(self, start, end):
        return self.GetTextRange(start, end)

    def GetSelection(self):
        return self.GetAnchor(), self.GetCurrentPos()

    def SetSelection(self, start, end):
        self.SetSelectionStart(start)
        self.SetSelectionEnd(end)

    def SelectLine(self, line):
        start = self.PositionFromLine(line)
        end = self.GetLineEndPosition(line)
        self.SetSelection(start, end)

    def SetUpEditor(self):
        """
        This method carries out the work of setting up the Code editor.
        It's seperate so as not to clutter up the init code.
        """
        import keyword

        self.SetLexer(stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, " ".join(keyword.kwlist))

        # Enable folding
        self.SetProperty("fold", "1")

        # Highlight tab/space mixing (shouldn't be any)
        self.SetProperty("tab.timmy.whinge.level", "1")

        # Set left and right margins
        self.SetMargins(2, 2)

        # Set up the numbers in the margin for margin #1
        self.SetMarginType(1, wx.stc.STC_MARGIN_NUMBER)
        # Reasonable value for, say, 4-5 digits using a mono font (40 pix)
        self.SetMarginWidth(1, 40)

        # Indentation and tab stuff
        self.SetIndent(4)                 # Proscribed indent size for wx
        self.SetIndentationGuides(True)   # Show indent guides
        self.SetBackSpaceUnIndents(True)  # Backspace unindents rather than delete 1 space
        self.SetTabIndents(True)          # Tab key indents
        self.SetTabWidth(4)               # Proscribed tab size for wx
        self.SetUseTabs(False)            # Use spaces rather than tabs, or TabTimmy will complain!
        # White space
        self.SetViewWhiteSpace(False)   # Don't view white space

        # EOL: Since we are loading/saving ourselves, and the
        # strings will always have \n's in them, set the STC to
        # edit them that way.
        self.SetEOLMode(wx.stc.STC_EOL_LF)
        self.SetViewEOL(False)

        # No right-edge mode indicator
        self.SetEdgeMode(stc.STC_EDGE_NONE)

        # Set up a margin to hold fold markers
        self.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)

        # Global default style
        if wx.Platform == '__WXMSW__':
            self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'fore:#000000,back:#FFFFFF,face:Space Mono')  # Courier New
        elif wx.Platform == '__WXMAC__':
            # DEBUG: if this looks fine on Linux too, remove the Mac-specific case
            # and use this whenever OS != MSW.
            self.StyleSetSpec(stc.STC_STYLE_DEFAULT,
                              'fore:#000000,back:#FFFFFF,face:Monaco')
        else:
            # print("DEBUG: Setup on Linux")
            defsize = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT).GetPointSize()
            # Courier, Space Mono, Source Pro Mono,
            self.StyleSetSpec(stc.STC_STYLE_DEFAULT, 'fore:#000000,back:#FFFFFF,face:Hack,size:%d' % defsize)
        """
        self.StyleSetBackground(stc.STC_STYLE_DEFAULT, Colour(200, 222, 40))
        self.StyleSetForeground(stc.STC_STYLE_DEFAULT, Colour(7, 0, 70))
        """
        # Clear styles and revert to default.
        self.StyleClearAll()

        # Following style specs only indicate differences from default.
        # The rest remains unchanged.

        # Line numbers in margin
        self.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER, 'fore:#000000,back:#99A9C2')
        # Highlighted brace
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACELIGHT, 'fore:#00009D,back:#FFFF00')
        # Unmatched brace
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACEBAD, 'fore:#00009D,back:#FF0000')
        # Indentation guide
        self.StyleSetSpec(wx.stc.STC_STYLE_INDENTGUIDE, "fore:#CDCDCD")

        # Python styles
        self.StyleSetSpec(wx.stc.STC_P_DEFAULT, 'fore:#000000')
        # Comments
        self.StyleSetSpec(wx.stc.STC_P_COMMENTLINE,  'fore:#008000,back:#F0FFF0')
        self.StyleSetSpec(wx.stc.STC_P_COMMENTBLOCK, 'fore:#008000,back:#F0FFF0')
        # Numbers
        self.StyleSetSpec(wx.stc.STC_P_NUMBER, 'fore:#008080')
        # Strings and characters
        self.StyleSetSpec(wx.stc.STC_P_STRING, 'fore:#800080')
        self.StyleSetSpec(wx.stc.STC_P_CHARACTER, 'fore:#800080')
        # Keywords
        self.StyleSetSpec(wx.stc.STC_P_WORD, 'fore:#000080,bold')
        # Triple quotes
        self.StyleSetSpec(wx.stc.STC_P_TRIPLE, 'fore:#800080,back:#FFFFEA')
        self.StyleSetSpec(wx.stc.STC_P_TRIPLEDOUBLE, 'fore:#800080,back:#FFFFEA')
        # Class names
        self.StyleSetSpec(wx.stc.STC_P_CLASSNAME, 'fore:#0000FF,bold')
        # Function names
        self.StyleSetSpec(wx.stc.STC_P_DEFNAME, 'fore:#008080,bold')
        # Operators
        self.StyleSetSpec(wx.stc.STC_P_OPERATOR, 'fore:#800000,bold')
        # Identifiers. I leave this as not bold because everything seems
        # to be an identifier if it doesn't match the above criterae
        self.StyleSetSpec(wx.stc.STC_P_IDENTIFIER, 'fore:#000000')

        # Caret color
        self.SetCaretForeground("BLUE")
        # Selection background
        # self.SetSelBackground(1, '#66CCFF')
        """
        self.SetBackgroundColour(Colour(200, 222, 40))
        self.SetForegroundColour(Colour(7, 0, 70))
        """

        self.SetSelBackground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT))
        self.SetSelForeground(True, wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))

    def RegisterModifiedEvent(self, event_handler):
        self.Bind(wx.stc.EVT_STC_CHANGE, event_handler)


# ---------------------------------------------------------------------------
# Constants for module versions

modOriginal = 0
modModified = 1
modDefault = modOriginal

# ---------------------------------------------------------------------------


def is_utf8_strict(data):
    try:
        decoded = data.decode('UTF-8')
    except UnicodeDecodeError:
        return False
    else:
        for ch in decoded:
            if 0xD800 <= ord(ch) <= 0xDFFF:
                return False
        return True


class CodeEditorPanel(wx.Panel):
    """Panel for the 'Code Editor' tab"""
    def __init__(self, parent, main_frame, filepath=None):
        self.log = sys.stdout  # From FileDialog
        self.path = filepath
        wx.Panel.__init__(self, parent, size=(1, 1))
        self.mainFrame = main_frame
        self.editor = SourceCodeEditor(self, options={'tab markers':True, 'fold symbols':2})
        self.editor.RegisterModifiedEvent(self.on_code_modified)
        parent.SetName(f'Code Editor: {filepath}')
        """
        self.SetBackgroundColour(Colour(200, 222, 40))
        self.SetOwnBackgroundColour(Colour(200, 222, 40))
        self.SetForegroundColour(Colour(7, 0, 70))
        self.SetOwnForegroundColour(Colour(7, 0, 70))
        """

        self.btnSave = wx.Button(self, -1, "Save Changes")
        self.btnSave.Enable(False)
        self.btnSave.Bind(wx.EVT_BUTTON, self.on_save)

        # From FileDialog
        self.btnOpen = wx.Button(self, -1, "Open...")
        self.btnOpen.Bind(wx.EVT_BUTTON, self.on_button)

        self.btnSaveAs = wx.Button(self, -1, "Save as...")
        self.btnSaveAs.Bind(wx.EVT_BUTTON, self.on_button2)
        self.controlBox = wx.BoxSizer(wx.HORIZONTAL)
        self.controlBox.Add(self.btnSave, 0, wx.RIGHT, 5)
        self.controlBox.Add(self.btnOpen, 0, wx.RIGHT, 5)
        self.controlBox.Add(self.btnSaveAs, 0)

        self.box = wx.BoxSizer(wx.VERTICAL)
        self.box.Add(self.controlBox, 0, wx.EXPAND)
        self.box.Add(wx.StaticLine(self), 0, wx.EXPAND)
        self.box.Add(self.editor, 1, wx.EXPAND)

        self.box.Fit(self)
        self.SetSizer(self.box)
        if self.path:
            # print("DEBUG: path is init = %s" % self.path)
            self.LoadFile(self.path)

    def LoadFile(self, filepath):
        # Open
        f = open(filepath, "rb")
        try:
            source = f.read()
        finally:
            f.close()
        self.LoadSource(source)

    def LoadSource(self, source):
        self.editor.Clear()
        self.editor.SetTextRaw(source)  # DEBUG SetValue
        self.JumpToLine(0)
        self.btnSave.Enable(False)

    def JumpToLine(self, line, highlight=False):
        self.editor.GotoLine(line)
        self.editor.SetFocus()
        if highlight:
            self.editor.SelectLine(line)

    def on_code_modified(self, event):
        __ = event
        self.btnSave.Enable(self.editor.IsModified())

    def on_save(self, event, filepath=None):
        if self.path is None:
            self.path = "noname"
            self.on_button2(event)
            return
        if filepath:
            if filepath != self.path and os.path.isfile(filepath):
                overwrite_msg = "You are about to overwrite an existing file\n" + \
                               "Do you want to continue?"
                dlg = wx.MessageDialog(self, overwrite_msg, "Editor Writer",
                                       wx.YES_NO | wx.NO_DEFAULT | wx.ICON_EXCLAMATION)
                dlg.SetBackgroundColour(Colour(200, 222, 40))
                dlg.SetForegroundColour(Colour(7, 0, 70))
                result = dlg.ShowModal()
                if result == wx.ID_NO:
                    return
                dlg.Destroy()
            self.path = filepath

        # Save
        f = open(self.path, "wb")
        source = self.editor.GetTextRaw()
        # print("DEBUG: Test is Unicode %s",isUTF8Strict(source))
        if is_utf8_strict(source):
            try:
                f.write(source)
                # print("DEBUG: Saved as Unicode")
            finally:
                f.close()
        else:
            # print("DEBUG: there were problems with source not being Unicode.")
            # Attempt to isolate the problematic bytes
            # DEBUG bytearray(source)
            try:
                chunksize = 1024
                for c in range(0, len(source), chunksize):
                    data = [chr(int(x, base=2)) for x in source[c:c + chunksize]]
                    f.write(b''.join(data))
            finally:
                f.close()

    def on_button(self, evt):
        _ = evt
        # Create the dialog. In this case the current directory is forced as the starting
        # directory for the dialog, and no default file name is forced. This can easilly
        # be changed in your program. This is an 'open' dialog, and allows multitple
        # file selections as well.
        #
        # Finally, if the directory is changed in the process of getting files, this
        # dialog is set up to change the current working directory to the path chosen.
        if self.path:
            cwd = os.path.dirname(self.path)
        else:
            cwd = os.getcwd()
        dlg = wx.FileDialog(
            self, message="Choose a file",
            defaultDir=cwd,
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_CHANGE_DIR | wx.FD_FILE_MUST_EXIST | wx.FD_PREVIEW)  # wx.FD_MULTIPLE |

        # Show the dialog and retrieve the user response. If it is the OK response,
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            # This returns a Python list of files that were selected.
            paths = dlg.GetPaths()

            # self.log.WriteText('You selected %d files:' % len(paths))
            # DEBUG self.log.write('You selected %d files:' % len(paths))

            filepath = paths[-1]  # just get the last one
            # Open
            f = open(filepath, "rb")
            try:
                source = f.read()
            finally:
                f.close()

            # store the new path
            self.path = filepath
            # self.log.write('%s\n' % source)
            self.LoadSource(source)  # Just the last file
        # Compare this with the debug above; did we change working dirs?
        # self.log.WriteText("CWD: %s\n" % os.getcwd())
        # self.log.write("CWD: %s\n" % os.getcwd())

        # Destroy the dialog. Don't do this until you are done with it!
        # BAD things can happen otherwise!
        dlg.Destroy()

    def on_button2(self, evt):
        # Create the dialog. In this case the current directory is forced as the starting
        # directory for the dialog, and no default file name is forced. This can easilly
        # be changed in your program. This is an 'save' dialog.
        #
        # Unlike the 'open dialog' example found elsewhere, this example does NOT
        # force the current working directory to change if the user chooses a different
        # directory than the one initially set.
        fname = ""
        if self.path:
            cwd = os.path.dirname(self.path)
            fname = os.path.basename(self.path)
        else:
            cwd = os.getcwd()
            self.path = "noname"
        dlg = wx.FileDialog(
            self, message="Save file as ...", defaultDir=cwd,
            defaultFile=fname, wildcard=wildcard, style=wx.FD_SAVE
            )  # | wx.FD_OVERWRITE_PROMPT

        # This sets the default filter that the user will initially see. Otherwise,
        # the first filter in the list will be used by default.
        # dlg.SetFilterIndex(2)

        # Show the dialog and retrieve the user response. If it is the OK response,
        # process the data.
        if dlg.ShowModal() == wx.ID_OK:
            filepath = dlg.GetPath()
            # Normally, at this point you would save your data using the file and path
            # data that the user provided to you, but since we didn't actually start
            # with any data to work with, that would be difficult.
            #
            # The code to do so would be similar to this, assuming 'data' contains
            # the data you want to save:
            #
            # fp = file(path, 'w') # Create file anew
            # fp.write(data)
            # fp.close()
            #
            # You might want to add some error checking :-)
            #
            # store the new path
            # self.path = path
            self.on_save(evt, filepath)
        # Note that the current working dir didn't change. This is good since
        # that's the way we set it up.
        # self.log.WriteText("CWD: %s\n" % os.getcwd())
        # self.log.write("CWD: %s\n" % os.getcwd())

        # Destroy the dialog. Don't do this until you are done with it!
        # BAD things can happen otherwise!
        dlg.Destroy()


# ---------------------------------------------------------------------------

def opj(filepath):
    """Convert paths to the platform-specific separator"""
    st = os.path.join(*tuple(filepath.split('/')))
    # HACK: on Linux, a leading / gets lost...
    if filepath.startswith('/'):
        st = '/' + st
    return st


def get_data_dir():
    """
    Return the standard location on this platform for application data
    """
    sp = wx.StandardPaths.Get()
    return sp.GetUserDataDir()


def get_modified_directory():
    """
    Returns the directory where modified versions of the Code files
    are stored
    """
    return os.path.join(get_data_dir(), "modified")


def get_modified_filename(name):
    """
    Returns the filename of the modified version of the specified Code
    """
    if not name.endswith(".py"):
        name = name + ".py"
    return os.path.join(get_modified_directory(), name)


def get_original_filename(name):
    """
    Returns the filename of the original version of the specified Code
    """
    if not name.endswith(".py"):
        name = name + ".py"

    if os.path.isfile(name):
        return name

    original_dir = os.getcwd()
    list_dir = os.listdir(original_dir)
    # Loop over the content of the Code directory
    for item in list_dir:
        if not os.path.isdir(item):
            # Not a directory, continue
            continue
        dir_file = os.listdir(item)
        # See if a file called "name" is there
        if name in dir_file:
            return os.path.join(item, name)

    # We must return a string...
    return ""


def does_modified_exist(name):
    """Returns whether the specified Code has a modified copy"""
    if os.path.exists(get_modified_filename(name)):
        return True
    else:
        return False


def get_config():
    if not os.path.exists(get_data_dir()):
        os.makedirs(get_data_dir())

    config = wx.FileConfig(
        localFilename=os.path.join(get_data_dir(), "options"))
    return config


_platformNames = ["wxMSW", "wxGTK", "wxMac"]


def main(filepath, frame=None):
    __name__ = f'Code Editor: {filepath}'
    app = wx.App()
    app.SetAppDisplayName(__name__)
    if frame is None:
        frame = wx.Frame(None)
    CodeEditorPanel(frame, None, filepath)
    frame.Show(True)
    app.MainLoop()
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------


if __name__ == '__main__' and __package__ is None:
    from os import path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    path = None
    try:
        if sys.argv[1]:
            path = sys.argv[1]
    except IndexError:
        pass
    finally:
        main(path)
# ----------------------------------------------------------------------------
