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

def get_core_plugins():
    from ..run import RunAnything
    from ..recentfiles import RecentFilesPlugin
    from ..ui.keywordsearch import KeywordSearch
    from ..ui.treeplugin import TreePlugin
    from ..ui.fileexplorerplugin import FileExplorerPlugin
    from ..editor import EditorPlugin
    from ..editor.texteditor import TextEditorPlugin
    from ..log import LogPlugin
    from ..parserlog import ParserLogPlugin
    from ..searchtests.searchtests import TestSearchPlugin
    from ..spec.specimporter import SpecImporterPlugin
    from ..postinstall.desktopshortcut import ShortcutPlugin

    return [LogPlugin, RunAnything, RecentFilesPlugin, SpecImporterPlugin, EditorPlugin, TextEditorPlugin,
            KeywordSearch, TestSearchPlugin, ShortcutPlugin, ParserLogPlugin, TreePlugin, FileExplorerPlugin]
