.. container:: document

   `RIDE (Robot Framework
   IDE) <https://github.com/robotframework/RIDE/>`__ v2.2 is a new
   release with some enhancements and bug fixes. The reference for valid
   arguments is `Robot Framework <https://robotframework.org/>`__
   current version, 7.3.2. However, internal library code is originally
   based on version 3.1.2, but adapted for new versions.

   -  This version supports Python 3.8 up to 3.13 (and also tested on
      3.14.rc3 with wxPython 4.2.3).
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

   **New Features and Fixes Highlights**

   -  Fixed duplicated resources in Tree (Project Explorer).
   -  Added Project Settings concept. The Project Settings is a file
      named **ride_settings.cfg** inside a directory named **.robot**
      located in the Test Suite directory.
   -  Fixed crash when renaming test cases names on Tree (Project
      Explorer), by cancelling with Escape or by adding a Space in the
      end.
   -  Fixed missing text colorization in suites and test settings on
      Grid Editor.
   -  Restored init and main scripts and texteditor, because some
      changes in Grid Editor were not being saved in Text Editor and
      would be lost.
   -  Fix faulty cell editor in settings of Grid Editor which would
      prevent to change to Text Editor and Run tabs.
   -  Added indication of **private** keywords in Grid Editor, keywords
      will show in *Italic*, and with error background, when they are
      used outside of Keywords section, or from different files.
   -  Added indication of **private** keywords in Details pop-up for
      keywords with tag **robot:private** or name starting with
      underscore, **'\_'** in Grid Editor.
   -  Modified the action of key TAB when selecting from
      auto-suggestions list in Grid Editor. Pressing TAB, selects the
      item and continues in cell editor.
   -  Fix cursor position when editing cells in Grid Editor.
   -  Added parsing of option **--name** or **-N** and **Name** setting,
      to allow running tests with them set.

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

      pip install --upgrade robotframework-ride==2.2

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

   RIDE v2.2 was released on 05/October/2025.

   .. rubric:: Celebrate the bank holiday, 5th October, Implantation of
      the Republic in Portugal
      :name: celebrate-the-bank-holiday-5th-october-implantation-of-the-republic-in-portugal

   .. rubric:: Happy 115th bithday! Long live the Republic!
      :name: happy-115th-bithday-long-live-the-republic

   .. rubric:: 🇵🇹
      :name: section
