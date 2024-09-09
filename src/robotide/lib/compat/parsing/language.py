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

try:
    from robot.conf.languages import Language
except ImportError as e:
    sys.stderr.write(f"Trying to import robot's languages module returned error: {repr(e)}\n")
    sys.stderr.write("You need to have Robot Framework v6.0 or newer to use languages in test suites.\n")
    try:
        # Using local copy of https://github.com/robotframework/robotframework/blob/v7.0.1/src/robot/conf/languages.py
        from .languages import Language
    except ImportError:
        Language = None
from robot.errors import DataError
from robotide.lib.robot.utils import Utf8Reader


def check_file_language(path):
    """
    Returns the language code if defined and valid, error if not valid, or None if file does not have preamble.

    :param path: Path to robot or resource file
    :return: language, error or None
    """
    if not Language:
        return None
    language_string = None
    if os.path.isfile(path):
        language_string = read(path)
    if not language_string:
        return None
    # If preamble exists, proceed with language detection
    try:
        from robot.conf.languages import Languages
    except ImportError as err:
        sys.stderr.write(f"Trying to import robot's languages module returned error: {repr(err)}\n")
        try:
            from .languages import Languages
        except ImportError:
            return None
    try:
        build_lang = Languages(language_string, add_english=False)
    except (DataError, ModuleNotFoundError) as err:
        sys.stderr.write(f"File language definition returned error: {repr(err)}\n")
        return None
    if build_lang:
        # print(f"DEBUG: check_file_language {build_lang.settings}\n{build_lang.headers}\n{build_lang.true_strings}"
        #      f"\n{build_lang.false_strings}\n{build_lang.bdd_prefixes}")
        lang = []
        for ll in build_lang:
            lang.append(ll.code.replace('-', '_'))
        return lang


def get_language_name(lang_code):
    """
    Returns the language name if valid from name or code.

    :param lang_code: language code or name
    :return: language name or None
    """
    if lang_code and len(lang_code) < 2:
        return None
    if not Language or not lang_code:
        return None
    try:
        from robot.conf.languages import Languages
    except ImportError as err:
        sys.stderr.write(f"Trying to import robot's languages module returned error: {repr(err)}\n")
        try:
            from .languages import Languages
        except ImportError:
            return None
    try:
        build_lang = Languages(lang_code.replace('_', '-'), add_english=False)
    except (DataError, ModuleNotFoundError) as err:
        sys.stderr.write(f"File language definition returned error: {repr(err)}\n")
        return None
    if build_lang:
        for lang in build_lang:
            return lang.name


def read(path):
    lang = None
    for lineno, line in enumerate(Utf8Reader(path).readlines(), start=1):
        row = line.rstrip()
        if row and row.strip().startswith('*'):
            break
        else:
            if row.startswith('Language:'):
                content = row.split('#')
                if len(content) > 1:
                    content = content[0]
                else:
                    content = row
                lang = content[len('Language:'):].strip()
                mlang = lang.split(',')
                if len(mlang) > 1:
                    lang = mlang[:]
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
    # print(f"DEBUG: language.py get_headers_for ENTER {language=} tables_headers={tables_headers}")
    if not Language:
        return t_en
    assert tables_headers is not None
    if not language:
        language = ['en']
    languages = set()
    for mlang in language:
        try:
            if not mlang:
                mlang = 'en'
            lang = Language.from_name(mlang.replace('_', '-'))
            languages.add(lang)
        except ValueError:
            print(f"DEBUG: language.py get_headers_for Exception at language={mlang}")

    tables_headers = [item.lower() for item in list(tables_headers)] if lowercase else tables_headers
    if not languages:
        # print("DEBUG: language.py get_headers_for languages set is empty returning original tables_headers")
        return tables_headers
    # print(f"DEBUG: language.py get_headers_for BEFORE BUILD TABLE {language=} tables_headers={tables_headers}")
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
                except Exception as ex:
                    print(f"DEBUG: robotide.lib.compat.parsing.language.py get_headers: {ex}")
                    pass
                inx += 1
            for bh in build_headings:
                build_table.add(bh)
    # print(f"DEBUG: language.py get_headers_for BEFORE RE-BUILD TABLE build_table= {build_table}")
    mod_headers = list(tables_headers)
    if build_table:
        new_table = list(build_table)
        for k in new_table:
            if k in mod_headers:
                mod_headers.remove(k)
        for th in mod_headers:
            if th != '':
                new_table.append(th)
        # print(f"DEBUG: language.py get_headers_for RETURN table= {new_table}")
        return tuple(new_table)
    # print(f"DEBUG: language.py get_headers_for RETURN AFTER FAILED BUILD TABLE tables_headers={tables_headers}")
    return tables_headers


def get_settings_for(language, settings_names):
    assert settings_names is not None
    if not Language:
        return settings_names
    if not language or len(language) == 0:
        language = ['en']
    languages = set()
    if isinstance(language, list):
        for mlang in language:
            try:
                if not mlang:
                    mlang = 'en'
                lang = Language.from_name(mlang.replace('_', '-'))
                languages.add(lang)
            except (ValueError, AttributeError):
                return settings_names
                # print(f"DEBUG: language.py get_settings_for Exception at language={mlang}")
    else:
        lang = Language.from_name(language.replace('_', '-'))
        languages.add(lang)
    # DEBUG: settings_names = [item.lower() for item in list(settings_names)]
    if not languages:
        print("DEBUG: language.py get_settings_for languages set is empty")
        return {}

    build_table = {}
    for lang in languages:
        settings = lang.settings
        for item in settings_names:
            inx = 0
            for k, v in zip(settings.keys(), settings.values()):
                try:
                    if v.lower() == item.lower():
                        setting = list(settings.keys())[inx]
                        build_table[setting] = item
                        break
                except Exception as ex:
                    print(f"DEBUG: robotide.lib.compat.parsing.language.py get_settings: {ex}")
                    pass
                inx += 1
    #  print(f"DEBUG: language.py get_settings_for RETURN build_table={build_table}")
    return build_table


def get_english_label(lang, label):
    assert label is not None
    if not Language:
        return label
    if not lang:
        lang = ['en']
    mlang = None
    if isinstance(lang, list):
        try:
            mlang = Language.from_name(lang[0].replace('_', '-'))  # Only care for a single language
        except ValueError:
            print(f"DEBUG: language.py get_english_label Exception at language={lang}")
    else:
        mlang = Language.from_name(lang.replace('_', '-'))
    if not mlang:
        print(f"DEBUG: language.py get_english_label lang={lang} not found")
        return None
    setting_names = list(mlang.settings.keys())
    try:
        index = setting_names.index(label)
    except ValueError:
        # print(f"DEBUG: language.py get_english_label Exception at getting index {lang} returning={label}")
        return label
    en_label = list(mlang.settings.values())[index]
    return en_label


def get_localized_setting(language: [], english_name: str):
    if not language:
        return english_name
    settings = get_settings_for(language, (english_name,))
    try:
        result = list(settings.keys())[list(settings.values()).index(english_name)]
    except ValueError:
        return english_name
    return result
