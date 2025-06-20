# RIDE

RIDE is an IDE (Integrated Development Environment) exclusive for [Robot Framework](https://robotframework.org) tests or tasks automation framework.

----

Robot Framework supports, since version 6.1, files with localized definitions. RIDE was updated to accept those files, and we are working on a localization project to have its GUI in the same languages supported by Robot Framework.
You can help in this localization project at [Crowdin](https://crowdin.com/project/robotframework-ride) [![Crowdin](https://badges.crowdin.net/robotframework-ride/localized.svg)](https://crowdin.com/project/robotframework-ride)


### Instant Communication

Join our **#ride** channel in Robot Framework Slack: https://robotframework.slack.com
(signup page, with insecure connection warning: https://slack.robotframework.org/)

### "Support" sites

We have a RIDE section topic in [Tools>RIDE](https://forum.robotframework.org/c/tools/ride/21).

You can use the tag *robotframework-ide* to search and ask on [StackOverflow](https://stackoverflow.com/questions/tagged/robotframework-ide).

## **Welcome to RIDE - next major release will be version 2.2**

If you are looking for the latest released version, you can get the source code from **[releases](https://github.com/robotframework/RIDE/releases)** or from branch **[release/2.1.4](https://github.com/robotframework/RIDE/tree/release/2.1.4)**

See the [release notes](https://github.com/robotframework/RIDE/blob/master/doc/releasenotes/ride-2.1.4.rst) for latest release version 2.1.4

**Version [2.0.8.1](https://github.com/robotframework/RIDE/tree/release/2.0.8.1) was the last release supporting Python 3.6 and 3.7**

**Version [1.7.4.2](https://github.com/robotframework/RIDE/tree/release/1.7.4.2) was the last release supporting Python 2.7**


**The current development version is based on 2.1.3, supports Python from 3.8 up to 3.14 (20th June 2025).**

Currently, the unit tests are tested on Python 3.10, 3.11 and 3.13 (3.13 is the recommended version).
We now have an experimental workflow on Fedora Linux 41, with wxPython 4.2.3 and Python 3.14.a7.
Likewise, the current version of wxPython, is 4.2.3, but RIDE is known to work with 4.0.7, 4.1.1 and 4.2.2 versions.

(3.8 &lt;= python &lt;= 3.14) Install current released version (*2.1.4*) with:

`pip install -U robotframework-ride`

(3.8 &lt;= python &lt;= 3.14) Install current development version (**2.2dev??**) with:

`pip install -U https://github.com/robotframework/RIDE/archive/develop.zip`

**See the [FAQ](https://github.com/robotframework/RIDE/wiki/F%2eA%2eQ%2e) at [Wiki](https://github.com/robotframework/RIDE/wiki)**



## Unit testing statuses:

Linux (Fedora 41: py3.13, Ubuntu 22.04: py3.10): [[!Linux](https://img.shields.io/github/actions/workflow/status/HelioGuilherme66/RIDE/linux.yml)](https://github.com/HelioGuilherme66/RIDE/actions/workflows/linux.yml)

Windows (Python 3.11): [[!Windows](https://ci.appveyor.com/api/projects/status/github/HelioGuilherme66/RIDE?branch=master&svg=true)](https://ci.appveyor.com/project/HelioGuilherme66/ride)

Quality Gate Status: [[!Sonar](https://sonarcloud.io/api/project_badges/measure?project=HelioGuilherme66_RIDE&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=HelioGuilherme66_RIDE)

----
### Links

* [Localization at Crowdin](https://crowdin.com/project/robotframework-ride)
* [Downloads at PyPi](https://pypi.python.org/pypi/robotframework-ride)
* Statistics at [PyPi Stats](https://pypistats.org/packages/robotframework-ride) and [Libraries.io](https://libraries.io/pypi/robotframework-ride)
* Usage instructions and some tips and tricks can be found from the [Wiki](https://github.com/robotframework/RIDE/wiki)
* Bug report/enhancement request? Use the [issue tracker](https://github.com/robotframework/RIDE/issues)
* Any questions? Do not hesitate to use the [mailing list](https://groups.google.com/group/robotframework-users/), or [Robot Framework Forum->Tools>RIDE](https://forum.robotframework.org/c/tools/ride/21), or [StackOverflow](https://stackoverflow.com/questions/tagged/robotframework-ide).
* Development information is in [BUILD](https://github.com/robotframework/RIDE/blob/master/BUILD.rest) file

---

## Stargazers over time

[[!Stargazers over time](https://starchart.cc/robotframework/RIDE.svg)]
