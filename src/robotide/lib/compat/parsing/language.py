#  Copyright 2023-     Robot Framework Foundation
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
import sys

from robotide.lib.robot.utils import Utf8Reader


def check_file_language(path):
    """
    Returns the language code if defined and valid, error if not valid, or None if file does not have preamble.

    :param path: Path to robot or resource file
    :return: language, error or None
    """
    language_string = read(path)
    if not language_string:
        return None
    # If preamble exists, proceed with language detection
    try:
        from robot.conf.languages import Languages
    except ImportError as e:
        sys.stderr.write(f"Trying to import robot's languages module returned error: {repr(e)}\n")
        return None
    build_lang = Languages(language_string, add_english=False)
    if build_lang:
        print(f"DEBUG: check_file_language {build_lang.settings}\n{build_lang.headers}\n{build_lang.true_strings}"
              f"\n{build_lang.false_strings}\n{build_lang.bdd_prefixes}")
        lang = []
        for ll in build_lang:
            lang.append(ll.code)
        return lang


def read(path):
    lang = None
    for lineno, line in enumerate(Utf8Reader(path).readlines(), start=1):
        row = line.rstrip()
        if row and row.strip().startswith('*'):
            break
        else:
            if row.startswith('Language:'):
                lang = row[len('Language:'):].strip()
    return lang
