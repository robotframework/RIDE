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
import os.path
import sys

from robot.conf.languages import Language
from robot.errors import DataError
from robotide.lib.robot.utils import Utf8Reader


def check_file_language(path):
    """
    Returns the language code if defined and valid, error if not valid, or None if file does not have preamble.

    :param path: Path to robot or resource file
    :return: language, error or None
    """
    language_string = None
    if os.path.isfile(path):
        language_string = read(path)
    if not language_string:
        return None
    # If preamble exists, proceed with language detection
    try:
        from robot.conf.languages import Languages
    except ImportError as e:
        sys.stderr.write(f"Trying to import robot's languages module returned error: {repr(e)}\n")
        return None
    try:
        build_lang = Languages(language_string, add_english=False)
    except (DataError, ModuleNotFoundError) as e:
        sys.stderr.write(f"File language definition returned error: {repr(e)}\n")
        return None
    if build_lang:
        # print(f"DEBUG: check_file_language {build_lang.settings}\n{build_lang.headers}\n{build_lang.true_strings}"
        #      f"\n{build_lang.false_strings}\n{build_lang.bdd_prefixes}")
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


def get_headers_for(language, tables_headers, lowercase=True):
    _setting_table_names = 'Setting', 'Settings'
    _variable_table_names = 'Variable', 'Variables'
    _testcase_table_names = 'Test Case', 'Test Cases', 'Task', 'Tasks'
    _keyword_table_names = 'Keyword', 'Keywords'
    _comment_table_names = 'Comment', 'Comments'
    t_en = [(_setting_table_names,),
            (_variable_table_names,),
            (_testcase_table_names,),
            (_keyword_table_names,),
            (_comment_table_names,)]
    assert tables_headers is not None
    if not language:
        language = ['en']
    languages = set()
    for mlang in language:
        try:
            lang = Language.from_name(mlang)
            languages.add(lang)
        except ValueError:
            print(f"DEBUG: language.py get_headers_for Exception at language={mlang}")

    tables_headers = [item.lower() for item in list(tables_headers)] if lowercase else tables_headers
    if not languages:
        # print("DEBUG: language.py get_headers_for languages set is empty returning original tables_headers")
        return tables_headers

    build_table = set()
    for lang in languages:
        headers = lang.headers
        # print(f"DEBUG: language.py get_headers_for HEADERS headers={headers}, table_headers={tables_headers}")
        for item in tables_headers:
            build_headings = []
            inx = 0
            for k, v in zip(headers.keys(), headers.values()):
                try:
                    if v.lower() == item.lower():
                        header = list(headers.keys())[inx].lower() if lowercase else list(headers.keys())[inx]
                        build_headings.append(header)
                        break
                except Exception as e:
                    pass
                inx += 1
            for bh in build_headings:
                build_table.add(bh)
    if build_table:
        # print(f"DEBUG: language.py get_headers_for returning table= {build_table}")
        for th in tables_headers:
            build_table.add(th)
        return tuple(list(build_table))
    return tables_headers
