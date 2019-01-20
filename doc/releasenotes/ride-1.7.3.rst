=========================
Robot Framework IDE 1.7.3
=========================


.. default-role:: code


`RIDE (Robot Framework IDE)`_ 1.7.3 is a new release with major enhancements
and bug fixes. It contains some updates for `Robot Framework`_ version 3.1.1.

The most notable enhancements are:
..................................
* Compatible with Python 2.7 and >=3.6
* Runs with "any" wxPython version (2.8.12.1, 3.0.2 on Python 2.7)
  and 4.0.4 for both Python 2.7 and >=3.6
* Runner can select new or old versions of Robot Framework (``pybot` vs ``robot``)
* Panes, Tabs, Toolbar are detachable and re-positionable thanks to wxPython's AUI module
* Text Editor now have a autocomplete feature
* Test cases on tree pane, have the new official icon, and is animated when running or paused
* Long test names on tree pane, have name shortened by ... and name visible on tool-tip
* On tree pane at test suite level, context menu allows to open folder in file manager,
  and to remove the Read-Only file attribute
* If no tests are selected there will be a confirmation to proceed with running all tests
* Like F8 to run tests, now there is F9 to run them with log level DEBUG
* The Grid Editor now have a JSON editor for a cell (it validates when saving)

Unfortunately, this release may introduce new bugs, unknown or known like the ones:
------------------------------------------------------------------------------------
* On Windows to call autocomplete in Grid Editor, you have to use Ctrl-Alt-Space, (or keep using Ctrl-Space after disabling Text Editor)
* On Windows 10, in Grid Editor, when you select text on a cell, the selection, although valid, is not visible
* On some Linuxes (Fedora 28, for example), when you click No in some Dialog boxes, there is the repetition of those Dialogs
* On some Linuxes the new validation of test suites, may complaint about HTML format, and this makes not opening the folders. You have to select a single file, kill RIDE and restart it.
* Problems with non UTF-8 console encodings may cause output problems

(and more for you to find out ;) )

All issues targeted for RIDE v1.7.3 can be found
from the `issue tracker milestone`_.

Questions and comments related to the release can be sent to the
`robotframework-users`_ mailing list or to the channel #ride on 
`Robot Framework Slack`_, and possible bugs submitted to the `issue tracker`_.

If you have pip_ installed, just run

::

   pip install --upgrade robotframework-ride

to install (or upgrade) the latest available release or use

::

   pip install robotframework-ride==1.7.3

to install exactly this version. Alternatively you can download the source
distribution from PyPI_ and install it manually. You may want to see the
document `BUILD.rest`_ for other details.

RIDE 1.7.3 was released on Sunday January 20, 2019.

.. _RIDE (Robot Framework IDE): https://github.com/robotframework/RIDE/
.. _Robot Framework: http://robotframework.org
.. _pip: http://pip-installer.org
.. _PyPI: https://pypi.python.org/pypi/robotframework-ride
.. _issue tracker milestone: https://github.com/robotframework/RIDE/issues?q=milestone%3Av1.7.3
.. _issue tracker: https://github.com/robotframework/RIDE/issues
.. _robotframework-users: http://groups.google.com/group/robotframework-users
.. _Robot Framework Slack: https://robotframework-slack-invite.herokuapp.com
.. _BUILD.rest: ../../BUILD.rest


.. contents::
   :depth: 2
   :local:

Full list of fixes and enhancements
===================================

.. list-table::
    :header-rows: 1

    * - ID
      - Type
      - Priority
      - Summary
    * - `#1416`_
      - bug
      - ---
      - When saving in the Text Edit screen, all test case checkboxes are cleared
    * - `#1556`_
      - bug
      - ---
      - Rename GIVEN WHEN THEN keywords does not work properly
    * - `#1588`_
      - bug
      - ---
      - Problems with tests selection from View All Tags dialog
    * - `#1594`_
      - bug
      - ---
      - Inefective Delete tag button in View All Tags dialog
    * - `#1598`_
      - bug
      - ---
      - RIDE fails to load (traceback generated) if a plugin fails
    * - `#1605`_
      - bug
      - ---
      - Find Usages not working for variables definitions
    * - `#1578`_
      - ---
      - ---
      - Fixes `#1576`_.
    * - `#1580`_
      - ---
      - ---
      - Improves Sort trailing numbers in tag names numerically ...
    * - `#1584`_
      - ---
      - ---
      - Changed code to be PEP8 compliant and removed unnecessary method
    * - `#1586`_
      - ---
      - ---
      - Bugfix `#1416`_: test case checkbox cleard upon save in textedit
    * - `#1595`_
      - ---
      - ---
      - Adds --version option to RIDE.
    * - `#1597`_
      - ---
      - ---
      - Creates desktop shortcuts for all platforms.
    * - `#1599`_
      - ---
      - ---
      - Update BrokenPlugin to RF 2.9's get_error_details method
    * - `#1600`_
      - ---
      - ---
      - Fixes `#1556`_, by ignoring starting Gherkin keywords.
    * - `#1604`_
      - ---
      - ---
      - Fix dictionary var rename from tree `#1603`_.
    * - `#1606`_
      - ---
      - ---
      - Fix finding usages of variables (`#1605`_).
    * - `#1610`_
      - ---
      - ---
      - Wx python3 compatibility
    * - `#1612`_
      - ---
      - ---
      - View all tags: fix delete functionality
    * - `#1613`_
      - ---
      - ---
      - Fixes viewalltags dialog to show tags with unicode characters.
    * - `#1616`_
      - ---
      - ---
      - Renames editor/grid.py to editor/gridbase.py as discussed at `#1611`_.
    * - `#1631`_
      - ---
      - ---
      - Confirmation dialog when pressing start without tests selected
    * - `#1655`_
      - ---
      - ---
      - Added "Run with Debug" hotkey  F9
    * - `#1663`_
      - ---
      - ---
      - Added context menu items
    * - `#1664`_
      - ---
      - ---
      - Adds a JSON Editor for a Grid Cell content
    * - `#1677`_
      - ---
      - ---
      - fix crash in Linux after popup window was detached
    * - `#1679`_
      - ---
      - ---
      - Adds "context" to invoke>=0.13 methods.
    * - `#1698`_
      - ---
      - ---
      - Direct pythonpath order
    * - `#1733`_
      - ---
      - ---
      - Prevent an exception-handling routine from failing with pythonw
    * - `#1777`_
      - ---
      - ---
      - Auto Keyword suggestion for RIDE iDE not working on MAC
    * - `#1789`_
      - ---
      - ---
      - New master to release version 1.7.3

Altogether 30 issues. View on the `issue tracker <https://github.com/robotframework/RIDE/issues?q=milestone%3Av1.7.3>`__.

.. _#1416: https://github.com/robotframework/RIDE/issues/1416
.. _#1556: https://github.com/robotframework/RIDE/issues/1556
.. _#1588: https://github.com/robotframework/RIDE/issues/1588
.. _#1594: https://github.com/robotframework/RIDE/issues/1594
.. _#1598: https://github.com/robotframework/RIDE/issues/1598
.. _#1605: https://github.com/robotframework/RIDE/issues/1605
.. _#1578: https://github.com/robotframework/RIDE/issues/1578
.. _#1576: https://github.com/robotframework/RIDE/issues/1576
.. _#1580: https://github.com/robotframework/RIDE/issues/1580
.. _#1584: https://github.com/robotframework/RIDE/issues/1584
.. _#1586: https://github.com/robotframework/RIDE/issues/1586
.. _#1595: https://github.com/robotframework/RIDE/issues/1595
.. _#1597: https://github.com/robotframework/RIDE/issues/1597
.. _#1599: https://github.com/robotframework/RIDE/issues/1599
.. _#1600: https://github.com/robotframework/RIDE/issues/1600
.. _#1603: https://github.com/robotframework/RIDE/issues/1603
.. _#1604: https://github.com/robotframework/RIDE/issues/1604
.. _#1606: https://github.com/robotframework/RIDE/issues/1606
.. _#1610: https://github.com/robotframework/RIDE/issues/1610
.. _#1611: https://github.com/robotframework/RIDE/issues/1611
.. _#1612: https://github.com/robotframework/RIDE/issues/1612
.. _#1613: https://github.com/robotframework/RIDE/issues/1613
.. _#1616: https://github.com/robotframework/RIDE/issues/1616
.. _#1631: https://github.com/robotframework/RIDE/issues/1631
.. _#1655: https://github.com/robotframework/RIDE/issues/1655
.. _#1663: https://github.com/robotframework/RIDE/issues/1663
.. _#1664: https://github.com/robotframework/RIDE/issues/1664
.. _#1677: https://github.com/robotframework/RIDE/issues/1677
.. _#1679: https://github.com/robotframework/RIDE/issues/1679
.. _#1698: https://github.com/robotframework/RIDE/issues/1698
.. _#1733: https://github.com/robotframework/RIDE/issues/1733
.. _#1777: https://github.com/robotframework/RIDE/issues/1777
.. _#1789: https://github.com/robotframework/RIDE/issues/1789
