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

import unittest

from utest.resources import datafilereader
from robotide.lib.compat.parsing import language


class TestLanguage(unittest.TestCase):

    def test_check_file_without_preamble(self):
        lang = language.check_file_language(datafilereader.SIMPLE_PROJECT)
        assert lang is None

    def test_check_file_with_preamble_no_lang(self):
        lang = language.check_file_language(datafilereader.PREAMBLE_NO_LANG)
        assert lang is None

    def test_check_file_with_preamble_unknown_lang(self):
        lang = language.check_file_language(datafilereader.PREAMBLE_UNKNOWN_LANG)
        assert lang is None

    def test_check_file_lang_bg(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_BG)
        assert lang == ['bg']

    def test_check_file_lang_bs(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_BS)
        assert lang == ['bs']

    def test_check_file_lang_cs(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_CS)
        assert lang == ['cs']

    def test_check_file_lang_de(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_DE)
        assert lang == ['de']

    def test_check_file_lang_es(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_ES)
        assert lang == ['es']

    def test_check_file_lang_en(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_EN)
        assert lang == ['en']

    def test_check_file_lang_fr(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_FR)
        assert lang == ['fr']

    def test_check_file_lang_fi(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_FI)
        assert lang == ['fi']

    def test_check_file_lang_hi(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_HI)
        assert lang == ['hi']

    def test_check_file_lang_it(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_IT)
        assert lang == ['it']

    def test_check_file_lang_nl(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_NL)
        assert lang == ['nl']

    def test_check_file_lang_pl(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_PL)
        assert lang == ['pl']

    def test_check_file_lang_pt_br(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_PT_BR)
        assert lang == ['pt-BR']

    def test_check_file_lang_pt(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_PT)
        assert lang == ['pt']

    def test_check_file_lang_ro(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_RO)
        assert lang == ['ro']

    def test_check_file_lang_RU(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_RU)
        assert lang == ['ru']

    def test_check_file_lang_sv(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_SV)
        assert lang == ['sv']

    def test_check_file_lang_th(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_TH)
        assert lang == ['th']

    def test_check_file_lang_tr(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_TR)
        assert lang == ['tr']

    def test_check_file_lang_uk(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_UK)
        assert lang == ['uk']

    def test_check_file_lang_vi(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_VI)
        assert lang == ['vi']

    def test_check_file_lang_zh_cn(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_ZH_CN)
        assert lang == ['zh-CN']

    def test_check_file_lang_zh_tw(self):
        lang = language.check_file_language(datafilereader.VALID_LANG_ZH_TW)
        assert lang == ['zh-TW']

    def test_get_headers_unknown_language_lw(self):
        headers = language.get_headers_for(['Pirates'], ['Settings'])
        assert list(headers) == ['settings']

    def test_get_headers_unknown_language(self):
        headers = language.get_headers_for(['Pirates'], ['Settings'], lowercase=False)
        assert list(headers) == ['Settings']

    def test_get_headers_known_language_lw(self):
        headers = language.get_headers_for(['pt'], ['Settings'])
        assert sorted(headers) == ['definições', 'settings']

    def test_get_headers_known_language(self):
        headers = language.get_headers_for(['pt-BR'], ['Settings'], lowercase=False)
        assert sorted(headers) == ['Configurações', 'Settings']

    def test_get_headers_multiple_languages_lw(self):
        headers = language.get_headers_for(['es', 'fr', 'Chinese Simplified ', 'zh-TW'], ['Settings'], lowercase=True)
        assert sorted(headers) == ['configuraciones', 'paramètres', 'settings', '設置', '设置']

    def test_get_headers_multiple_languages(self):
        headers = language.get_headers_for(['pt-BR', 'pt', 'Pirates', 'en'], ['Settings'], lowercase=False)
        assert sorted(headers) == ['Configurações', 'Definições', 'Settings']


if __name__ == '__main__':
    unittest.main()
