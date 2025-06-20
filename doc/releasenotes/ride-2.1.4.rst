.. container:: document

   `RIDE (Robot Framework
   IDE) <https://github.com/robotframework/RIDE/>`__ v2.1.4 is a new
   release with some enhancements and bug fixes. The reference for valid
   arguments is `Robot Framework <https://robotframework.org/>`__
   current version, 7.3.1. However, internal library code is originally
   based on version 3.1.2, but adapted for new versions.

   -  This version supports Python 3.8 up to 3.13 (and also tested on
      3.14.a7 with wxPython 4.2.3).
   -  There are some changes, or known issues:

      -  🐞 - Rename Keywords, Find Usages/Find where used are not
         finding all occurrences. Please, double-check findings and
         changes.
      -  🐞 - Some argument types detection (and colorization) is not
         correct in Grid Editor.
      -  🐞 - RIDE **DOES NOT KEEP** Test Suites formatting or
         structure, causing differences in files when used on other IDE
         or Editors. The option to not reformat the file is not working.
      -  🐞 - In Grid Editor, when showing settings, scrolling down with
         mouse or using down is not working. You can change to Text
         Editor and back to Grid Editor, to restore normal behavior.

   **New Features and Fixes Highlights**

   -  Added **Tools->Library Finder...** to install libraries and
      **Help->Open Library Documentation...** . They share the same
      dialog, and definitions are recorded in \``settings.cfg`\`.
   -  Added context menu to install libraries and to open documentation
      in Grid Editor Import section. Same as above description.
   -  Added keyboard shortcuts **Ctrl-Shift-Up** and **Ctrl-Shift-Down**
      as alternatives to **Alt-Up** and **Alt-Down** to move rows in
      Grid and Text Editors.
   -  Improved vertical scroll in Grid Editor, by having main scroll
      bars out of cells.
   -  Fixed Create Desktop Shortcut by pointing executable to **python
      -m robotide**.
   -  Changed arguments parser to allow **--version** and **--help**
      functional in Windows.
   -  Improved auto-complete in Grid Editor, to allow several matches.
   -  Fixed white blocks on Tree due to failed animation when test
      execution is too rapid, causing crash on Windows.
   -  Added Settings Editor button to Preferences dialog, to edit
      settings.cfg.
   -  Created backup of settings.cfg to allow recovering some settings
      when broken upgrades.
   -  Changed some informative dialogs and JSON Editor to use the
      customized colors.
   -  Added current executing keyword and other statuses to TestRunner
      status bar.
   -  Modified import statements to allow running RIDE without Robot
      Framework installed or versions older than 6.0.
   -  Added Config Panel button to supported installed Plugins next to
      their name in Plugin Manager dialog.
   -  Added Config Panel button to Plugins, working examples in Text
      Editor and Test Runner.
   -  On Windows ignore false modification on files when opening Test
      Suites, causing confirmation dialog.
   -  Added divided Status Bar. Left side for main window, right side
      for Plugins. Working example in Text Editor, when selecting in
      Tree shows the filename in StatusBar.

   **The minimal wxPython version is, 4.0.7, and RIDE supports the
   current version, 4.2.3, which we recommend.**

   *Linux users are advised to install first wxPython from .whl package
   at*
   `wxPython.org <https://extras.wxpython.org/wxPython4/extras/linux/gtk3/>`__,
   or by using the system package manager.

   The
   `CHANGELOG.adoc <https://github.com/robotframework/RIDE/blob/master/CHANGELOG.adoc>`__
   lists the changes done on the different versions.

   All issues targeted for RIDE v2.2 can be found from the `issue
   tracker
   milestone <https://github.com/robotframework/RIDE/issues?q=milestone%3Av2.2>`__.

   Questions and comments related to the release can be sent to the
   `robotframework-users <https://groups.google.com/group/robotframework-users>`__
   mailing list or to the channel #ride on `Robot Framework
   Slack <https://robotframework-slack-invite.herokuapp.com>`__, and
   possible bugs submitted to the `issue
   tracker <https://github.com/robotframework/RIDE/issues>`__. You
   should see `Robot Framework
   Forum <https://forum.robotframework.org/c/tools/ride/>`__ if your
   problem is already known.

   To install the latest release with
   `pip <https://pypi.org/project/pip/>`__ installed, just run

   .. code:: literal-block

      pip install --upgrade robotframework-ride==2.1.4

   to install exactly the specified release, which is the same as using

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

      pip install -U https://github.com/robotframework/RIDE/archive/develop.zip

   Important document for helping with development is the
   `CONTRIBUTING.adoc <https://github.com/robotframework/RIDE/blob/develop/CONTRIBUTING.adoc>`__.

   To start RIDE from a command window, shell or terminal, just enter:

   ::

      ride

   You can also pass some arguments, like a path for a test suite file
   or directory.

   ::

      ride example.robot

   Another possible way to start RIDE is:

   .. code:: literal-block

      python -m robotide

   You can then go to Tools>Create RIDE Desktop Shortcut, or run the
   shortcut creation script with:

   .. code:: literal-block

      python -m robotide.postinstall -install

   or

   .. code:: literal-block

      ride_postinstall.py -install

   RIDE v2.1.4 was released on 20/June/2025.
