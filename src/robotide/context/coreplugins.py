def get_core_plugins():
    from robotide.application.releasenotes import ReleaseNotesPlugin
    from robotide.ui.recentfiles import RecentFilesPlugin
    from robotide.ui.preview import PreviewPlugin
    from robotide.editor import EditorPlugin, Colorizer

    return [ReleaseNotesPlugin, RecentFilesPlugin, PreviewPlugin, Colorizer,
            EditorPlugin]
