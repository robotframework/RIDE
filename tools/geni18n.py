# -*- coding: utf-8 -*-
"""
This will generate the .pot and .mo files for the application domain and
languages defined below.

The .po and .mo files are placed as per convention in

"appfolder/localization/lang/LC_MESSAGES"

The .pot file is placed in the localization folder.

This script or something similar should be added to your build process.

The actual translation work is normally done using a tool like poEdit or
similar, it allows you to generate a particular language catalog from the .pot
file or to use the .pot to merge new translations into an existing language
catalog.

"""


# we remove English as source code strings are in English
supportedLang = ['bg_BG', 'da_DK', 'es_ES', 'hi_IN', 'it_IT', 'ja_JP', 'ko_KR', 'pl_PL', 'sv_SE', 'uk_UA', 'zh_TW', 'bs_BA',
                 'de_DE', 'fi_FI', 'hu_HU', 'pt_BR', 'ro_RO', 'th_TH', 'tr_TR', 'vi_VN', 'cs_CZ', 'en_US', 'fr_FR', 'nl_NL',
                 'pt_PT', 'ru_RU', 'zh_CN' ]

# for l in appC.supLang:
#     if l != u"en":
#         supportedLang.append(l)

import os
import re
import sys
import shutil
import subprocess
from pathlib import Path


# DEBUG: appFolder = os.getcwd()
# DEBUG: appFolder = os.path.join(appFolder, '../src/robotide')
# appFolder = '/home/helio/github/RIDE/src/robotide'
appFolder = (Path(__file__).parent / ".." / "src" / "robotide").resolve()
langDomain = 'RIDE'

# setup some stuff to get at Python I18N tools/utilities

pyExe = sys.executable
pyFolder = os.path.split(pyExe)[0]
if os.path.isfile('/etc/redhat-release'):  # In Fedora 42, install `sudo dnf install python-devel`
    pyI18nFolder = '/usr/bin'
else:
    pyI18nFolder = os.path.join(pyFolder, 'Tools', 'i18n')
pyGettext = os.path.join(pyI18nFolder, 'pygettext.py')
pyMsgfmt = os.path.join(pyI18nFolder, 'msgfmt.py')
outFolder = os.path.join(appFolder, 'localization')
potFile = os.path.join(outFolder, '%s.pot' % langDomain)


def rm_empty_comments(fpath):
    '''Remove empty location comments prefixed with "#: " in the `.pot` file.'''
    with open(fpath, 'r+', encoding='utf-8') as f:
        lines = [l for l in f if l.strip() != '#:']
        f.seek(0)
        f.writelines(lines)
        f.truncate()

def rm_domain_prefix(fpath):
    '''Remove the RIDE domain path prefix from location comments in the `.pot` file.'''
    # use GNU style (`#: `) for location comments
    pattern = re.compile(r'^#: (.*):(\d+)$')
    with open(fpath, 'r', encoding='utf-8') as fin:
        lines = fin.readlines()
    
    with open(fpath, 'w', encoding='utf-8') as fout:
        for line in lines:
            m = pattern.match(line)
            if m:
                filename, lineno = m.groups()
                # unify separators to forward slash (/).
                filename_std = filename.replace('\\', '/')
                # remove 'RIDE' and the parts before it (compatibility `/` and `\`).
                idx = filename_std.find('RIDE/')
                if idx != -1:
                    cleaned = filename_std[idx + len('RIDE/'):]
                else:
                    cleaned = filename_std
                fout.write(f'#: {cleaned}:{lineno}\n')
            else:
                fout.write(line)

def convert_pot_charset(fpath):
    '''Convert the charset of `.pot` file to `UTF-8`.
    
    This is useful on Windows, where pygettext may generates `.pot` file 
    in a different charset, potentially causing encoding issues that 
    result in a runtime error with msgmerge.'''
    potFile = Path(fpath)
    if not potFile.exists():
        raise FileNotFoundError(f'{fpath} Not Exists.')
    raw = potFile.read_bytes()
    fixed = re.sub(
        rb'("Content-Type:\s*text/plain;\s*charset=)[^\\n"]+',
        rb'\1UTF-8',
        raw,
        flags=re.IGNORECASE
    )
    potFile.write_bytes(fixed)


# build command for pygettext
gtOptions = '-a -d %s -o %s.pot -p %s %s'
tCmd = pyExe + ' ' + pyGettext + ' ' + (gtOptions % (langDomain,
                                                     langDomain,
                                                     outFolder,
                                                     appFolder))
print("Generating the .pot file")
print("cmd: %s" % tCmd)
rCode = subprocess.call(tCmd.split(' '))
print("return code: %s" % rCode)

# sCmd = f"sed -i -r -e /\\^\\#\\:\\$/d {potFile}"
# print(f"Command sed: {sCmd}")
# rCode = subprocess.call(sCmd.split(' '))
# print("AFTER REMOVING EMPTY COMMENTS: return code: %s\n\n" % rCode)
convert_pot_charset(potFile)
rm_empty_comments(potFile)
rm_domain_prefix(potFile)


# Merge the existing.po file with the new.pot template using `msgmerge` 
# - Retain the existing translation
# - Add the newly added string in `.pot`
def show_install_guide():
    '''show `msgmerge` install guide.'''
    guide = """
===> TroubleShooting: msgmerge command not found <===

Solution:
    - Linux (Ubuntu/Debian): `sudo apt install gettext`
    - macOS:
        `brew install gettext`
        `export PATH="/usr/local/opt/gettext/bin:$PATH"`
    - Windows:
        Download gettext tool from https://mlocati.github.io/articles/gettext-iconv-windows.html
        Install it and add the `bin` directory to your PATH
    - For more information, visit https://www.gnu.org/software/gettext
    - It might be necessary to restart your IDE to make the PATH effective

Validation: `msgmerge --version`
"""
    print(guide)


if shutil.which("msgmerge") is None:
    print('\nError: The `msgmerge` command was not found in the system. Please install the gettext tool first.')
    show_install_guide()
    sys.exit(1)

# You may notice that location comments (#: filename:lineno) in `.po` file lose their original line breaks 
# are merged into a single line, separated by spaces (like `#: f1:n1 f2:n2`).
# This is not a bug but an intentional behavior of GNU gettext.
# Its goal is to be machine-readable rather than retaining the format when manually edited.
# And translation tools like PoEdit do not rely on line breaks.
def split_location_cmts(fpath):
    '''split the merged location comments.'''
    text = Path(fpath).read_text(encoding='utf-8')
    fixed = []
    for line in text.splitlines():
        if line.startswith('#: '):
            parts = line[3:].split()
            for p in parts:
                fixed.append(f'#: {p}')
        else:
            fixed.append(line)
    Path(fpath).write_text('\n'.join(fixed) + '\n', encoding='utf-8')

for tLang in supportedLang:
    # build command for msgfmt
    langDir = os.path.join(appFolder, 'localization', tLang, 'LC_MESSAGES')
    poFile = os.path.join(langDir, langDomain + '.po')

    if os.path.isfile(poFile):
        tCmd = 'msgmerge' + ' ' + '-U' + ' ' + poFile + ' ' + potFile
        print("Updating .po file with .pot\n")
        print("cmd: %s" % tCmd)
        rCode = subprocess.call(tCmd.split(' '))
        print("return code: %s" % rCode)
        # sCmd = f"sed -i -r -e /\\^\\#\\:\\$/d {poFile}"
        # rCode = subprocess.call(sCmd.split(' '))
        # print("AFTER REMOVING EMPTY COMMENTS: return code: %s\n\n" % rCode)
        split_location_cmts(poFile)

    tCmd = pyExe + ' ' + pyMsgfmt + ' ' + poFile
    print("Generating the .mo file")
    print("cmd: %s" % tCmd)
    rCode = subprocess.call(tCmd.split(' '))
    print("return code: %s\n\n" % rCode)
