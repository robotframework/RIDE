.. container:: document

   .. rubric:: RIDE is celebrating 16 years on this date!
      :name: ride-is-celebrating-16-years-on-this-date

   `RIDE (Robot Framework
   IDE) <https://github.com/robotframework/RIDE/>`__ v2.1 is a new
   release with important enhancements and bug fixes. The reference for
   valid arguments is `Robot Framework <https://robotframework.org/>`__
   installed version, which is at this moment 7.1. However, internal
   library code is originally based on version 3.1.2, but adapted for
   new versions.

   -  This version supports Python 3.8 up to 3.12.
   -  There are some changes, or known issues:

      -  ❌ - Removed support for Python 3.6 and 3.7
      -  ✔ - Fixed recognition of variables imported from YAML, JSON and
         Python files.
      -  ✔ - Added a setting for a specific Browser by editing the
         settings.cfg file. Add the string parameter **browser** in the
         section **[Plugins][[Test Runner]]**
      -  Fixed on Text Editor when Saving the selection of tests to run
         in Test Suites (Tree) is cleared.
      -  ✔ - Added Korean language support for UI.
      -  ✔ - Added **caret style** to change insert caret to 'block' or
         'line' in Text Editor, by editing *settings.cfg*. The color of
         the caret is the same as 'setting' and will be adjusted for
         better contrast with the background.
      -  ✔ - Allow to do auto-suggestions of keywords in Text Editor
         without a shortcut, if you want to enable or disable this
         feature you can config in \`Tools -> Preferences -> Text Editor
         -> Enable auto suggestions\`.
      -  ✔ - Added support for Setup in keywords, since Robot Framework
         version 7.0.
      -  ✔ - Added support for new VAR marker, since Robot Framework
         version 7.0.
      -  ✔ - Added to Grid Editor changing Zoom In/Out with **Ctrl-Mouse
         Wheel** and setting at Preferences.
      -  ✔ - Fixed plugin Run Anything (Macros) not showing output and
         broken actions.
      -  ✔ - Added actions on columns of Grid Editor: Double-Click or
         Right Mouse Click, allows to edit the column name for Data
         Driven or Templated; Left Mouse Click, selects the column
         cells.
      -  ✔ - Added command line option, **--settingspath**, to select a
         different configuration.
      -  ✔ - Added different settings file, according the actual Python
         executable, if not the original installed.
      -  ✔ - Added a selector for Tasks and Language to the New Project
         dialog.
      -  ✔ - Added UI localization prepared for all the languages from
         installed Robot Framework version 6.1, or higher. Major
         translations are: Dutch, Portuguese and Brazilian Portuguese.
         Still missing translation of some elements.
      -  ✔ - Added support for language configured test suites, with
         languages from installed Robot Framework version 6.1, or
         higher.
      -  ✔ - On Text Editor, pressing **Ctrl** when the caret/cursor is
         near a Keyword will show a detachable window with the
         documentation, at Mouse Pointer position.
      -  ✔ - RIDE tray icon now shows a context menu with options Show,
         Hide and Close.
      -  ✔ - Highlighting and navigation of selected Project Explorer
         items, in Text Editor.
      -  ✔ - When editing in Grid Editor with content assistance, the
         selected content can be edited by escaping the list of
         suggestions with keys ARROW_LEFT or ARROW_RIGHT.
      -  ✔ - Newlines in Grid Editor can be made visible with the
         **filter newlines** set to False.
      -  🐞 - Problems with COPY/PASTE in Text Editor have been reported
         when using wxPython 4.2.0, but not with version 4.2.1 and
         4.2.2, which we now *recommend*.
      -  🐞 - Some argument types detection (and colorization) is not
         correct in Grid Editor.
      -  🐞 - RIDE **DOES NOT KEEP** Test Suites formatting or
         structure, causing differences in files when used on other IDE
         or Editors.

   **New Features and Fixes Highlights**

   -  Fixed recognition of variables imported from YAML, JSON and Python
      files.
   -  Added a setting for a specific Browser by editing the settings.cfg
      file. Add the string parameter **browser** in the section
      **[Plugins][[Test Runner]]**
   -  Changed the order of insert and delete rows in Grid Editor rows
      context menu.
   -  Fixed validation of multiple arguments with default values in Grid
      Editor.
   -  Added color to Test Runner Console Log final output, report and
      log since RF v7.1rc1.
   -  Fixed on Text Editor when Saving the selection of tests to run in
      Test Suites (Tree) is cleared.
   -  Added Korean language support for UI, experimental.
   -  Fixed wrong item selection, like Test Suite, when doing
      right-click actions in Project Explorer.
   -  Fixed delete variable from Test Suite settings remaining in
      Project Explorer.
   -  Added **caret style** to change insert caret to 'block' or 'line'
      in Text Editor, by editing *settings.cfg*. The color of the caret
      is the same as 'setting' and will be adjusted for better contrast
      with the background.
   -  Fixed obsfuscation of Libraries and Metadata panels when expanding
      Settings in Grid Editor and Linux systems.
   -  Allow to do auto-suggestions of keywords in Text Editor without a
      shortcut, if you want to enable or disable this feature you can
      config in \`Tools -> Preferences -> Text Editor -> Enable auto
      suggestions\`.
   -  Added support for Setup in keywords, since Robot Framework version
      7.0.
   -  Fixed multiline variables in Variables section. In Text Editor
      they are separated by ... continuation marker. In Grid Editor use
      \| (pipe) to separate lines.
   -  Added support for new VAR marker, since Robot Framework version
      7.0.
   -  Added configurable style of the tabs in notebook pages, Edit,
      Text, Run, etc. Parameter **notebook theme** takes values from 0
      to 5. See wxPython, demo for agw.aui for details.
   -  Added UI localization and support for Japanese configured test
      suites, valid for Robot Framework version 7.0.1 or higher.
   -  Fixed keywords Find Usages in Grid Editor not finding certain
      values when using Gherkin.
   -  Improved selection of items from Tree in Text Editor. Now finds
      more items and selects whole line.
   -  Changed output in plugin Run Anything (Macros) to allow Zoom
      In/Out, and Copy content.
   -  Added to Grid Editor changing Zoom In/Out with **Ctrl-Mouse
      Wheel** and setting at Preferences.
   -  Fixed plugin Run Anything (Macros) not showing output and broken
      actions.
   -  Added actions on columns of Grid Editor: Double-Click or Right
      Mouse Click, allows to edit the column name for Data Driven or
      Templated; Left Mouse Click, selects the column cells.
   -  Added command line option, **--settingspath**, to select a
      different configuration.
   -  Added different settings file, according the actual Python
      executable, if not the original installed.
   -  Fixed headers and blank spacing in Templated tests.
   -  Added context option **Open Containing Folder** to test suites
      directories in Project Explorer.
   -  Added a setting for a specific file manager by editing the
      settings.cfg file. Add the string parameter **file manager** in
      the section **[General]**
   -  Added minimal support to have comment lines in Import settings.
      These are not supposed to be edited in Editor, and new lines are
      added at Text Editor.
   -  Fixed removal of continuation marker in steps
   -  Fixed wrong continuation of long chains of keywords in Setups,
      Teardowns or Documentation.
   -  Added a selector for Tasks and Language to the New Project dialog.
      Still some problems: Tasks type changes to Tests, localized
      sections only stay translated after Apply in Text Editor.
   -  Added UI localization prepared for all the languages from
      installed Robot Framework version 6.1, or higher. Language is
      selected from Tools->Preferences->General.
   -  Removed support for HTML file format (obsolete since Robot
      Framework 3.2)
   -  Added support for language configured test suites. Fields are
      shown in the language of the files in Grid Editor. Tooltips are
      always shown in English. Colorization for language configured
      files is working in Text Editor.
   -  Fixed New User Keyword dialog not allowing empty Arguments field
   -  Fixed escaped spaces showing in Text Editor on commented cells
   -  Improved keywords documentation search, by adding current dir to
      search
   -  Improved Move up/down, **Alt-UpArrow**/**Alt-DownArrow** in Text
      Editor, to have proper indentation and selection
   -  Added auto update check when development version is installed
   -  Added menu option **Help->Check for Upgrade** which allows to
      force update check and install development version
   -  Added **Upgrade Now** action to update dialog.
   -  Added **Test Tags** field (new, since Robot Framework 6.0) to Test
      Suites settings. This field will replace **Default** and **Force
      Tags** settings, after Robot Framework 7.0
   -  Improved **RIDE Log** and **Parser Log** windows to allow Zoom
      In/Out with **Ctrl-Mouse Wheel**
   -  Hide continuation markers in Project Tree
   -  Improved content assistance in Text Editor by allowing to filter
      list as we type
   -  Fixed resource files disappearing from Project tree on Windows
   -  Fixed missing indication of link for User Keyword, when pressing
      **Ctrl** in Grid Editor
   -  Added content help pop-up on Text Editor by pressing **Ctrl** for
      text at cursor position or selected autocomplete list item
   -  Added Exclude option in context nenu for Test files, previously
      was only possible for Test Suites folders
   -  Added exclusion of monitoring filesystem changes for files and
      directories excluded in Preferences
   -  Fixed exception when finding GREY color for excluded files and
      directories in Project Tree
   -  Added support for JSON variables, by using the installed Robot
      Framework import method
   -  Colorization of Grid Editor cells after the continuation marker
      **...** and correct parsing of those lines
   -  Colorization of Grid Editor cells when contents is list or
      dictionary variables
   -  Added indication of matching brackets, **()**, **{}**, **[]**, in
      Text Editor
   -  Fixed non synchronized expanding/collapse of Settings panel in
      Grid Editor, on Linux
   -  Fixed not working the deletion of cells commented with **#** in
      Grid Editor with **Ctrl-Shift-D**
   -  Fixed empty line being always added to the Variables section in
      Text Editor
   -  Improved project file system changes and reloading
   -  Added context menu to RIDE tray icon. Options Show, Hide and Close
   -  Added synchronization with Project Explorer to navigate to
      selected item, Test Case, Keyword, Variable, in Text Editor
   -  Control commands (**FOR**, **IF**, **TRY**, etc) will only be
      colorized as valid keywords when typed in all caps in Grid Editor
   -  Newlines in Grid Editor can be made visible with the **filter
      newlines** set to False, by editing *settings.cfg*
   -  Improve auto-suggestions of keywords in Grid Editor by allowing to
      close suggestions list with keys ARROW_LEFT or ARROW_RIGHT
   -  Improve Text Editor auto-suggestions by using: selected text, text
      at left or at right of cursor

   **The minimal wxPython version is, 4.0.7, and RIDE supports the
   current version, 4.2.2, which we recommend.**

   *Linux users are advised to install first wxPython from .whl package
   at*
   `wxPython.org <https://extras.wxpython.org/wxPython4/extras/linux/gtk3/>`__,
   or by using the system package manager.

   The
   `CHANGELOG.adoc <https://github.com/robotframework/RIDE/blob/master/CHANGELOG.adoc>`__
   lists the changes done on the different versions.

   All issues targeted for RIDE v2.1 can be found from the `issue
   tracker
   milestone <https://github.com/robotframework/RIDE/issues?q=milestone%3Av2.1>`__.

   Questions and comments related to the release can be sent to the
   `robotframework-users <https://groups.google.com/group/robotframework-users>`__
   mailing list or to the channel #ride on `Robot Framework
   Slack <https://robotframework-slack-invite.herokuapp.com>`__, and
   possible bugs submitted to the `issue
   tracker <https://github.com/robotframework/RIDE/issues>`__. You
   should see `Robot Framework
   Forum <https://forum.robotframework.org/c/tools/ride/>`__ if your
   problem is already known.

   To install with `pip <https://pypi.org/project/pip/>`__ installed,
   just run

   .. code:: literal-block

      pip install --upgrade robotframework-ride==v2.1

   to install exactly this release, which is the same as using

   .. code:: literal-block

      pip install --upgrade robotframework-ride

   Alternatively you can download the source distribution from
   `PyPI <https://pypi.python.org/pypi/robotframework-ride>`__ and
   install it manually. For more details and other installation
   approaches, see the `installation
   instructions <https://github.com/robotframework/RIDE/wiki/Installation-Instructions>`__.
   If you want to help in the development of RIDE, by reporting issues
   in current development version, you can install with:

   .. code:: literal-block

      pip install -U https://github.com/robotframework/RIDE/archive/master.zip

   Important document for helping with development is the
   `CONTRIBUTING.adoc <https://github.com/robotframework/RIDE/blob/master/CONTRIBUTING.adoc>`__.

   See the `FAQ <https://github.com/robotframework/RIDE/wiki/F.A.Q.>`__
   for important info about : FOR changes and other known issues and
   workarounds.

   To start RIDE from a command window, shell or terminal, just enter:

   ::

      ride

   You can also pass some arguments, like a path for a test suite file
   or directory.

   ::

      ride example.robot

   Another possible way to start RIDE is:

   .. code:: literal-block

      python -m robotide.__init__

   You can then go to Tools>Create RIDE Desktop Shortcut, or run the
   shortcut creation script with:

   .. code:: literal-block

      python -m robotide.postinstall -install

   or

   .. code:: literal-block

      ride_postinstall.py -install

   RIDE v2.1 was released on 13/October/2024 (`16 years after its first
   version <https://github.com/robotframework/RIDE/wiki/Old-Release-Notes%0A#ride-010>`__).
