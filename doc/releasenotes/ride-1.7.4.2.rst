===========================
Robot Framework IDE 1.7.4.2
===========================


.. default-role:: code


`RIDE (Robot Framework IDE)`_ 1.7.4.2 is a maintenance fix for version 1.7.4.1, due to latest upgrade of wxPython to version 4.1.0.

The only change on this version is making the wxPython version locked up to 4.0.7.post2.
There are no backported fixes, to Python 2.7 from Python 3.7.

This version 1.7.4.2 and 1.7.4.1 includes fixes for documentation, duplicate resources on tree, resources import with directory prefix, select all in Grid Editor, and more.
The reference for valid arguments is `Robot Framework`_ version 3.1.2.

* See the `release_notes`_ for version 1.7.4 with the major changes on that version.

**THIS IS THE LAST RELEASE SUPPORTING PYTHON 2.7**

**Supported versions are PYTHON 2.7, 3.6 and 3.7**

**wxPython version 4.0.7.post2 is the maximum supported for this version**

*Linux users are advised to install first wxPython from .whl package at* `wxPython.org`_.


All issues targeted for RIDE v1.7.4.1 can be found
from the `issue tracker milestone`_.

Questions and comments related to the release can be sent to the
`robotframework-users`_ mailing list or to the channel #ride on 
`Robot Framework Slack`_, and possible bugs submitted to the `issue tracker`_.

If you have pip_ installed, just run

::

   pip install --upgrade robotframework-ride==1.7.4.2

to upgrade to this **final** release, or

::

   pip install --upgrade robotframework-ride

::

   pip install robotframework-ride==1.7.4.2

to install exactly this **final** version for a first time. Alternatively you can download the source
distribution from PyPI_ and install it manually. For more details and other
installation approaches, see the `installation instructions`_.
See the `FAQ`_ for important info about `: FOR` changes.

A possible way to start RIDE is:

::

    python -m robotide.__init__

You can then go to `Tools>Create RIDE Desktop Shortcut`, or run the shortcut creation script with:

::

    python -m robotide.postinstall -install

RIDE 1.7.4.2 was released on Tuesday April 28, 2020.

.. _RIDE (Robot Framework IDE): https://github.com/robotframework/RIDE/
.. _Robot Framework: http://robotframework.org
.. _pip: http://pip-installer.org
.. _PyPI: https://pypi.python.org/pypi/robotframework-ride
.. _issue tracker milestone: https://github.com/robotframework/RIDE/issues?q=milestone%3Av1.7.4.1
.. _issue tracker: https://github.com/robotframework/RIDE/issues
.. _robotframework-users: http://groups.google.com/group/robotframework-users
.. _Robot Framework Slack: https://robotframework-slack-invite.herokuapp.com
.. _installation instructions: https://github.com/robotframework/RIDE/wiki/Installation-Instructions
.. _wxPython.org: https://extras.wxpython.org/wxPython4/extras/linux/gtk3/
.. _FAQ: https://github.com/robotframework/RIDE/wiki/F.A.Q.
.. _release_notes: https://github.com/robotframework/RIDE/blob/master/doc/releasenotes/ride-1.7.4.rst


.. contents::
   :depth: 2
   :local:
