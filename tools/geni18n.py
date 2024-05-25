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
supportedLang = ['bg_BG', 'da_DK', 'es_ES', 'hi_IN', 'it_IT', 'pl_PL', 'sv_SE', 'uk_UA', 'zh_TW', 'bs_BA', 'de_DE', 'fi_FI',
                 'hu_HU', 'pt_BR', 'ro_RO', 'th_TH', 'tr_TR', 'vi_VN', 'cs_CZ', 'en_US', 'fr_FR', 'nl_NL', 'pt_PT', 'ru_RU', 'zh_CN' ]

# for l in appC.supLang:
#     if l != u"en":
#         supportedLang.append(l)

import os
import sys
import subprocess
from pathlib import Path

# DEBUG: appFolder = os.getcwd()
# DEBUG: appFolder = os.path.join(appFolder, '../src/robotide')
# appFolder = '/home/helio/github/RIDE/src/robotide'
appFolder = Path(__file__).parent / "../src/robotide"
langDomain = 'RIDE'

# setup some stuff to get at Python I18N tools/utilities

pyExe = sys.executable
pyFolder = os.path.split(pyExe)[0]
pyI18nFolder = os.path.join(appFolder, 'i18n')
pyGettext = os.path.join(pyFolder, 'pygettext.py')
pyMsgfmt = os.path.join(pyFolder, 'msgfmt.py')
outFolder = os.path.join(appFolder, 'localization')

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

sCmd = f"sed -i -r -e /\\^\\#\\:\\$/d {outFolder}/{langDomain}.pot"

print(f"Command sed: {sCmd}")

rCode = subprocess.call(sCmd.split(' '))
print("AFTER REMOVING EMPTY COMMENTS: return code: %s\n\n" % rCode)

for tLang in supportedLang:
    # build command for msgfmt
    langDir = os.path.join(appFolder, ('localization/%s/LC_MESSAGES' % tLang))
    poFile = os.path.join(langDir, langDomain + '.po')
    if os.path.isfile(poFile):
        tCmd = 'msgmerge' + ' ' + '-U' + ' ' + poFile + ' ' + outFolder + '/' + langDomain + '.pot'
        print("Updating .po file with .pot\n")
        print("cmd: %s" % tCmd)
        rCode = subprocess.call(tCmd.split(' '))
        print("return code: %s" % rCode)
        sCmd = f"sed -i -r -e /\\^\\#\\:\\$/d {poFile}"
        rCode = subprocess.call(sCmd.split(' '))
        print("AFTER REMOVING EMPTY COMMENTS: return code: %s\n\n" % rCode)

    tCmd = pyExe + ' ' + pyMsgfmt + ' ' + poFile
    print("Generating the .mo file")
    print("cmd: %s" % tCmd)
    rCode = subprocess.call(tCmd.split(' '))
    print("return code: %s\n\n" % rCode)
