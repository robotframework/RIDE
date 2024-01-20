# -*- coding: utf-8 -*-
#  Copyright 2024-     Robot Framework Foundation
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

from os.path import abspath, join, dirname
import re


def tr_credits(filename="TRANSLATORS.adoc"):
    """ Returns the list of translators taken from TRANSLATORS.adoc to be used in About dialog."""

    # Added parameter filename because of unit tests
    isref = re.compile("(http.*)(\\[.*])(:)(.*)")
    try:
        with open(join(dirname(abspath(__file__)), filename), 'r', encoding='utf-8') as trf:
            content = trf.readlines()
    except FileNotFoundError:
        return ""
    lines = []
    lines += ["<ul>\n"]
    for tr in content:
        if tr.startswith('-'):
            row = tr.strip('- ')
            href = isref.findall(row)
            if href:
                href = href[0]
                url = href[0]
                name = href[1].strip('[]')
                langs = href[-1].strip()
                row = f'<a href="{url}">{name}</a>: {langs}'
            lines += [f"<li>{row.strip()}</li>\n"]
    lines += ["</ul>"]

    return "".join(lines)
