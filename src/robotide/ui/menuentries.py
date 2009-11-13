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

from menu import MenuEntry, MenuSeparator


_menudata = """
File
Open, Open file containing tests, Ctrl-O
Open Directory, Open dir containing Robot files, Shift-Ctrl-O
Open Resource, Open a resource file, Ctrl-R
---
New Suite, Create a new top level suite, Ctrl-N
New Resource, Create New Resource File, Ctrl-Shift-N
---
Save, Save current suite or resource, Ctrl-S
Save All, Save all changes, Ctrl-Shift-S
---
Exit, Exit RIDE, Ctrl-Q

Tools
Manage Plugins, Please Implement
Search Keywords, Search keywords from libraries and resources 

Help
About, Information about RIDE
"""


def MenuEntries(component, data=_menudata, container=None):
    menu = None
    for row in data.splitlines():
        if not row:
            menu = None
        elif menu:
            yield Entry(component, menu, container, row)
        else:
            menu = row

def Entry(component, menu, container, row):
    if is_separator(row):
        return MenuSeparator(menu)
    return create_entry(component, menu, container, row)

def is_separator(row):
    return row.startswith('---')

def create_entry(component, menu, container, row):
    tokens = row.split(', ')
    if len(tokens) == 2:
        tokens.append('')
    name, doc, shortcut =  tokens
    if name.startswith('*'):
        name = name[1:]
    else:
        container = None
    action = getattr(component, 'On%s' % name.replace(' ', ''))
    return MenuEntry(menu, name, action, container, shortcut, doc)
