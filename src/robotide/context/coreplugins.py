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
    from robotide.run import RunAnything
    from robotide.recentfiles import RecentFilesPlugin
    from robotide.ui.preview import PreviewPlugin
    from robotide.ui.keywordsearch import KeywordSearch
    from robotide.editor import EditorPlugin
    from robotide.editor.texteditor import TextEditorPlugin
    from robotide.log import LogPlugin
    from robotide.parserlog import ParserLogPlugin
    from robotide.searchtests.searchtests import TestSearchPlugin
    from robotide.spec.specimporter import SpecImporterPlugin
    from robotide.postinstall.desktopshortcut import ShortcutPlugin

    return [RunAnything, RecentFilesPlugin, PreviewPlugin, SpecImporterPlugin,
            EditorPlugin, TextEditorPlugin, KeywordSearch, LogPlugin,
            TestSearchPlugin, ShortcutPlugin, ParserLogPlugin]
