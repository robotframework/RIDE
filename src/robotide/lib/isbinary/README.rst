=======================================================================================
These files were copied and adapted from https://github.com/djmattyg007/python-isbinary
=======================================================================================

-----

========
isbinary
========

.. image:: https://github.com/djmattyg007/python-isbinary/workflows/CI/badge.svg?branch=main
   :target: https://github.com/djmattyg007/freiner/actions?query=branch%3Amain+workflow%3ACI
   :alt: CI

.. image:: https://codecov.io/gh/djmattyg007/python-isbinary/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/djmattyg007/python-isbinary
   :alt: Coverage

.. image:: https://img.shields.io/pypi/v/isbinary.svg
   :target: https://pypi.org/pypi/isbinary
   :alt: PyPI

.. image:: https://img.shields.io/pypi/l/isbinary.svg
   :target: https://pypi.org/project/isbinary
   :alt: BSD License

.. image:: https://readthedocs.org/projects/isbinary/badge/?version=latest
   :target: https://isbinary.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

Lightweight pure Python package to guess whether a file is binary or text,
using a heuristic similar to Perl's `pp_fttext` and its analysis by @eliben.

* Free software: BSD license
* Documentation: https://isbinary.readthedocs.io/

Status
------

It works, and people are using this package in various places. But it doesn't cover all edge cases yet.

The code could be improved. Pull requests welcome! As of now, it is based on these snippets, but that may change:

* https://stackoverflow.com/questions/898669/how-can-i-detect-if-a-file-is-binary-non-text-in-python
* https://stackoverflow.com/questions/1446549/how-to-identify-binary-and-text-files-using-python
* https://code.activestate.com/recipes/173220/
* https://eli.thegreenplace.net/2011/10/19/perls-guess-if-file-is-text-or-binary-implemented-in-python/

Features
--------

Has tests for these file types:

* Text: .txt, .css, .json, .svg, .js, .lua, .pl, .rst
* Binary: .png, .gif, .jpg, .tiff, .bmp, .DS_Store, .eot, .otf, .ttf, .woff, .rgb

Has tests for numerous encodings.

Why?
----

You may be thinking, "I can write this in 2 lines of code?!"

It's actually not that easy. Here's a great article about how Perl's
heuristic to guess file types works: https://eli.thegreenplace.net/2011/10/19/perls-guess-if-file-is-text-or-binary-implemented-in-python/

And that's just where we started. Over time, we've found more edge cases and
our heuristic has gotten more complex.

Also, this package saves you from having to write and thoroughly test
your code with all sorts of weird file types and encodings, cross-platform.

History
-------

This is a long-term fork of `binaryornot <https://github.com/audreyfeldroy/binaryornot>`_. It was created in
May 2022 primarily because it appeared that upstream had been abandoned. There were a few other smaller issues:

1. Lack of type annotations.
2. Lack of stricter modern code quality tools used in CI.
3. Improved contributor experience by using Github Actions for CI.
4. Possibility for optimisation with optional dependency on `cchardet`.
5. Removal of Python 2 support, and explicit support for newer versions of Python 3.

Credits
-------

* Audrey and Danny Roy Greenfeld, as the previous maintainers of this code.
* Special thanks to Eli Bendersky (@eliben) for his writeup explaining the heuristic and his implementation, which this is largely based on.
* Source code from the portion of Perl's `pp_fttext` that checks for textiness: https://github.com/Perl/perl5/blob/v5.23.1/pp_sys.c#L3527-L3587
