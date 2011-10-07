#  Copyright 2008-2011 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import re
from UserDict import UserDict


_WHITESPACE_REGEXP = re.compile('\s+')


def normalize(string, ignore=[], caseless=True, spaceless=True):
    """Normalizes given string according to given spec.

    By default string is turned to lower case and all whitespace is removed.
    Additional characters can be removed by giving them in `ignore` list.
    """
    if spaceless:
        string = _WHITESPACE_REGEXP.sub('', string)
    if caseless:
        string = string.lower()
        ignore = [i.lower() for i in ignore]
    for ign in ignore:
        string = string.replace(ign, '')
    return string


def normalize_tags(tags):
    """Returns tags sorted and duplicates, empty, and NONE removed.

    If duplicate tags have different case/space, the one used first wins.
    """
    norm = NormalizedDict(((t, 1) for t in tags), ignore=['_'])
    for removed in '', 'NONE':
        if removed in norm:
            norm.pop(removed)
    return norm.keys()


class NormalizedDict(UserDict):
    """Custom dictionary implementation automatically normalizing keys."""

    def __init__(self, initial=None, ignore=[], caseless=True, spaceless=True):
        """Initializes with possible initial value and normalizing spec.

        Initial values can be either a dictionary or an iterable of name/value
        pairs. In the latter case items are added in the given order.

        Normalizing spec has exact same semantics as with `normalize` method.
        """
        UserDict.__init__(self)
        self._keys = {}
        self._normalize = lambda s: normalize(s, ignore, caseless, spaceless)
        if initial:
            self._add_initial(initial)

    def _add_initial(self, items):
        if hasattr(items, 'items'):
            items = items.items()
        for key, value in items:
            self[key] = value

    def update(self, dict=None, **kwargs):
        if dict:
            UserDict.update(self, dict)
            for key in dict:
                self._add_key(key)
        if kwargs:
            self.update(kwargs)

    def _add_key(self, key):
        nkey = self._normalize(key)
        self._keys.setdefault(nkey, key)
        return nkey

    def set(self, key, value):
        nkey = self._add_key(key)
        self.data[nkey] = value

    __setitem__ = set

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __getitem__(self, key):
        return self.data[self._normalize(key)]

    def pop(self, key):
        nkey = self._normalize(key)
        del self._keys[nkey]
        return self.data.pop(nkey)

    __delitem__ = pop

    def has_key(self, key):
        return self.data.has_key(self._normalize(key))

    __contains__ = has_key

    def keys(self):
        return [self._keys[nkey] for nkey in sorted(self._keys)]

    def __iter__(self):
        return iter(self.keys())

    def values(self):
        return [self[key] for key in self]

    def items(self):
        return [(key, self[key]) for key in self]

    def copy(self):
        copy = UserDict.copy(self)
        copy._keys = self._keys.copy()
        return copy

    def __str__(self):
        return str(dict(self.items()))
