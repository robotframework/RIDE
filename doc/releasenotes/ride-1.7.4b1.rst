===========================
Robot Framework IDE 1.7.4b1
===========================


.. default-role:: code


`RIDE (Robot Framework IDE)`_ 1.7.4b1 is a new release with major enhancements
and bug fixes. This version 1.7.4b1 includes fixes for installer and new File explorer.
The reference for valid arguments is `Robot Framework`_ version 3.1.2.

**THIS IS THE LAST RELEASE SUPPORTING PYTHON 2.7**

**wxPython will be updated to current version 4.0.6**

*Linux users are advised to install first wxPython from .whl package at* `wxPython.org`_.

All issues targeted for **final** RIDE v1.7.4 can be found
from the `issue tracker milestone`_.

Questions and comments related to the release can be sent to the
`robotframework-users`_ mailing list or to the channel #ride on 
`Robot Framework Slack`_, and possible bugs submitted to the `issue tracker`_.

See the `FAQ`_ for important info about `: FOR` changes.

If you have pip_ installed, just run

::

   pip install --upgrade robotframework-ride==1.7.4b1

to install this **BETA** release, 
and for the **final** release use

::

   pip install --upgrade robotframework-ride

::

   pip install robotframework-ride==1.7.4

to install exactly the **final** version. Alternatively you can download the source
distribution from PyPI_ and install it manually. For more details and other
installation approaches, see the `installation instructions`_.

A possible way to start RIDE is:

::

    python -m robotide.__init__
    
::

You can then go to `Tools>Create RIDE Desktop Shortcut`, or run the shortcut creation script with:

::

    python -m robotide.postinstall -install

::

RIDE 1.7.4b1 was released on Wednesday August 29, 2019.

.. _RIDE (Robot Framework IDE): https://github.com/robotframework/RIDE/
.. _Robot Framework: http://robotframework.org
.. _pip: http://pip-installer.org
.. _PyPI: https://pypi.python.org/pypi/robotframework-ride
.. _issue tracker milestone: https://github.com/robotframework/RIDE/issues?q=milestone%3Av1.7.4
.. _issue tracker: https://github.com/robotframework/RIDE/issues
.. _robotframework-users: http://groups.google.com/group/robotframework-users
.. _Robot Framework Slack: https://robotframework-slack-invite.herokuapp.com
.. _installation instructions: ../../BUILD.rst
.. _wxPython.org: https://extras.wxpython.org/wxPython4/extras/linux/gtk3/
.. _FAQ: https://github.com/robotframework/RIDE/wiki/F.A.Q.


.. contents::
   :depth: 2
   :local:

Full list of **expected** fixes and enhancements (**will be updated until final version**)
==========================================================================================

.. list-table::
    :header-rows: 1

    * - ID
      - Type
      - Priority
      - Summary
    * - `#1747`_
      - bug
      - ---
      - RIDE-1.7.2 the Simplified-Chinese displayed problem 
    * - `#1793`_
      - bug
      - ---
      - Dependencies are not installed along with RIDE
    * - `#1803`_
      - bug
      - ---
      - the new ride v1.7.3.1 can not support the project that chinese in path
    * - `#1804`_
      - bug
      - ---
      - The new ride v1.7.3.1 can not execute by pythonw.exe
    * - `#1806`_
      - bug
      - ---
      - Can't install RIDE 1.7.3.1 when using buildout
    * - `#1812`_
      - bug
      - ---
      - Unable to run test cases if # comment is commented
    * - `#1873`_
      - bug
      - ---
      - Please bring back tag wrapping
    * - `#1836`_
      - enhancement
      - ---
      - RIDE doesn't scroll to searched text in Text Edit view
    * - `#1805`_
      - ---
      - ---
      - The new ride v1.7.3.1 shortcut is not working on Windows 7
    * - `#1807`_
      - ---
      - ---
      - Fix `#1804`_
    * - `#1808`_
      - ---
      - ---
      - Adds more files to MANIFEST, specially requirements.txt. Fixes `#1806`_
    * - `#1819`_
      - ---
      - ---
      - Column sizing on Mac doesn't work.
    * - `#1838`_
      - ---
      - ---
      - Wip fix win encoding
    * - `#1845`_
      - ---
      - ---
      - Grid editor issues on new RIDE
    * - `#1848`_
      - ---
      - ---
      - fix cells size in Grid editor
    * - `#1861`_
      - ---
      - ---
      - Add a file explorer
    * - `#1862`_
      - ---
      - ---
      - Installer - Fixes installation to all OS
    * - `#1863`_
      - ---
      - ---
      - Cell Sizes fixes
    * - `#1864`_
      - ---
      - ---
      - Installer
    * - `#1865`_
      - ---
      - ---
      - Desktopshortcut removal of GUI
    * - `#1866`_
      - ---
      - ---
      - Fixes Commented cells with # on Pause parsing
    * - `#1880`_
      - ---
      - ---
      - Changes encoding. Fixes running chinese path in python2.7 under Windows
    * - `#1884`_
      - ---
      - ---
      - Fixes utf-8 arguments and include/exclude options in Python2.

Altogether 23 issues. View on the `issue tracker <https://github.com/robotframework/RIDE/issues?q=milestone%3Av1.7.4>`__.

.. _#1747: https://github.com/robotframework/RIDE/issues/1747
.. _#1793: https://github.com/robotframework/RIDE/issues/1793
.. _#1803: https://github.com/robotframework/RIDE/issues/1803
.. _#1804: https://github.com/robotframework/RIDE/issues/1804
.. _#1806: https://github.com/robotframework/RIDE/issues/1806
.. _#1812: https://github.com/robotframework/RIDE/issues/1812
.. _#1873: https://github.com/robotframework/RIDE/issues/1873
.. _#1836: https://github.com/robotframework/RIDE/issues/1836
.. _#1805: https://github.com/robotframework/RIDE/issues/1805
.. _#1807: https://github.com/robotframework/RIDE/issues/1807
.. _#1808: https://github.com/robotframework/RIDE/issues/1808
.. _#1819: https://github.com/robotframework/RIDE/issues/1819
.. _#1838: https://github.com/robotframework/RIDE/issues/1838
.. _#1845: https://github.com/robotframework/RIDE/issues/1845
.. _#1848: https://github.com/robotframework/RIDE/issues/1848
.. _#1861: https://github.com/robotframework/RIDE/issues/1861
.. _#1862: https://github.com/robotframework/RIDE/issues/1862
.. _#1863: https://github.com/robotframework/RIDE/issues/1863
.. _#1864: https://github.com/robotframework/RIDE/issues/1864
.. _#1865: https://github.com/robotframework/RIDE/issues/1865
.. _#1866: https://github.com/robotframework/RIDE/issues/1866
.. _#1880: https://github.com/robotframework/RIDE/issues/1880
.. _#1884: https://github.com/robotframework/RIDE/issues/1884
