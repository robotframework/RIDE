.. container:: document

   `RIDE (Robot Framework
   IDE) <https://github.com/robotframework/RIDE/>`__ v2.2.2 is a new
   release with some enhancements and bug fixes. The reference for valid
   arguments is `Robot Framework <https://robotframework.org/>`__
   current version, 7.4.1. However, internal library code is originally
   based on version 3.1.2, but adapted for new versions.

   -  This version supports Python 3.9 up to 3.14.
   -  There are some changes, or known issues:

      -  🐞 - Rename Keywords, Find Usages/Find where used are not
         finding all occurrences. Please, double-check findings and
         changes.
      -  🐞 - Some argument types detection (and colorization) is not
         correct in Grid Editor.
      -  🐞 - In Grid Editor, private keywords defined in test suites
         with **Name** setting, will show with error color even if used
         correctly in another local keyword.
      -  🐞 - RIDE **DOES NOT KEEP** Test Suites formatting or
         structure, causing differences in files when used on other IDE
         or Editors. The option to not reformat the file is not working.
      -  🐞 - In Grid Editor, when showing settings, scrolling down with
         mouse or using down is not working. You can change to Text
         Editor and back to Grid Editor, to restore normal behavior.
      -  🐞 - In Files Explorer, when in floating window, the files tree
         is not always using all available space. Do a small resize of
         window to redraw.
      -  🐞 - The Test Suites Explorer, may be visible or hidden with
         F12, or toggled floating/docked, but content may disappear. You
         should try to make it reappear by toggling Files Explorer, F11,
         or by editing **settings.cfg**.

   **New Features and Fixes Highlights**

   -  The Test Suites Explorer can be visible or hidden with F12
      (View->View Test Suites Explorer). Pane can be made floating or
      docked, by dragging or by double-clicking its top bar.
   -  In File Explorer opening non-text files is done by the operating
      system registered app.
   -  Added context menu to File Explorer, to Open test suites
      directories or test suites files (also with double-click).
   -  Added context menu option to Open Containing Folder, in operating
      system file explorer, or specific tool.
   -  Added Config Panel button to File Explorer plugin. Here, you can
      set the operating system file explorer, or specify other tool, the
      Font style, and Colors.
   -  Fixed persistence of the state docked/floating of File Explorer.
   -  Fixed Cut (Ctrl-X) when editing the content of a cell in Grid
      Editor, before was deleting all content.

   **The minimal wxPython version is, 4.0.7, and RIDE supports the
   current version, 4.2.4, which we recommend.**

   *Linux users are advised to install first wxPython from .whl package
   at*
   `wxPython.org <https://extras.wxpython.org/wxPython4/extras/linux/gtk3/>`__,
   or by using the system package manager.

   The
   `CHANGELOG.adoc <https://github.com/robotframework/RIDE/blob/master/CHANGELOG.adoc>`__
   lists the changes done on the different versions.

   All issues targeted for RIDE v2.3 can be found from the `issue
   tracker
   milestone <https://github.com/robotframework/RIDE/issues?q=milestone%3Av2.3>`__.

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

      pip install --upgrade robotframework-ride==2.2.2

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

   RIDE v2.2.2 was released on 06/January/2026.
