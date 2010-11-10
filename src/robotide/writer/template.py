#  Copyright 2008-2009 Nokia Siemens Networks Oyj
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

import os
import re

import htmltemplate


_table_re = '(<table\s[^>]*id=["\']?%s["\']?[^>]*>).*?(</table>)'
_settings_re = re.compile(_table_re % 'settings', re.IGNORECASE | re.DOTALL)
_variables_re = re.compile(_table_re % 'variables', re.IGNORECASE | re.DOTALL)
_testcases_re = re.compile(_table_re % 'testcases', re.IGNORECASE | re.DOTALL)
_keywords_re = re.compile(_table_re % 'keywords', re.IGNORECASE | re.DOTALL)
del _table_re
_meta_re = re.compile('''
<head.*          # allow match only inside head element
<meta\s+(        # allow name and content in any order
name=["\']?rf-template["\']?\s*|
content=["\']?true["\']?\s*
){2}/?>          # allows also name or content twice, but that's ok
.*</head>
''', re.IGNORECASE | re.DOTALL | re.VERBOSE)
charset_re = re.compile('<meta.* content="text/html; charset=(.*?)"', re.IGNORECASE)



def Template(data_path, name):
    # TODO: should the file be closed explicitly? same issue in htmltemplate.
    if data_path and os.path.isfile(data_path):
        tmpl = _get_template(open(data_path), htmltemplate.TEMPLATE)
    else:
        tmpl = htmltemplate.TEMPLATE
    return tmpl % {'NAME': name}



def _get_template(data_file, default_template, resource_file=False):
    content = []
    template_matches = False
    encoding = None
    for line in data_file.readlines():
        line, encoding = _process_line(line, encoding)
        content.append(line)
        if not template_matches and '</head>' in line.lower():
            if _meta_re.search(''.join(content)):
                template_matches = True
            else:
                break
    tmpl = template_matches and ''.join(content) or default_template
    if resource_file:
        tmpl = _testcases_re.sub('', tmpl)
    return tmpl

def _process_line(line, encoding):
    if encoding:
        return unicode(line, encoding), encoding
    return line, _parse_encoding(line)

def _parse_encoding(line):
    match = charset_re.match(line)
    return match.group(1) if match else None

def settings_table(table, content):
    return _table(_settings_re, table, content)

def variables_table(table, content):
    return _table(_variables_re, table, content)

def testcases_table(table, content):
    return _table(_testcases_re, table, content)

def keywords_table(table, content):
    return _table(_keywords_re, table, content)

def _table(table_re, table, content):
    replaced = _table_replacer(table)
    return table_re.sub(replaced, content)

def _table_replacer(content):
    content = content.strip()
    def repl(match):
        start, end = match.groups()
        parts = content and [start, content, end] or [start, end]
        return '\n'.join(parts)
    return repl
