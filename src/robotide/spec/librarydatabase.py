#  Copyright 2008-2012 Nokia Siemens Networks Oyj
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
import sqlite3
import time
from robotide.preferences.settings import SETTINGS_DIRECTORY
from robotide.spec.iteminfo import LibraryKeywordInfo

CREATION_SCRIPT = """\
CREATE TABLE libraries (id INTEGER PRIMARY KEY,
                        name TEXT,
                        arguments TEXT,
                        last_updated REAL);
CREATE TABLE keywords (name TEXT,
                       doc TEXT,
                       arguments TEXT,
                       library INTEGER,
                       FOREIGN KEY(library) REFERENCES libraries(id));
"""

#FIXME! SIDE-EFFECTS DURING IMPORTING!

DB_DIR = os.path.join(SETTINGS_DIRECTORY, 'ride')

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

DATABASE_FILE = os.path.join(DB_DIR, 'librarykeywords.db')

if not os.path.exists(DATABASE_FILE):
    connection = sqlite3.connect(DATABASE_FILE)
    connection.executescript(CREATION_SCRIPT)
    connection.commit()
    connection.close()


class LibraryDatabase(object):

    def __init__(self, database):
        self._connection = sqlite3.connect(database)

    def create_database(self):
        self._connection.executescript(CREATION_SCRIPT)

    def close(self):
        self._connection.close()

    def insert_library_keywords(self, library_name, library_arguments, keywords):
        self._remove_old_versions(library_name, library_arguments)
        lib = self._insert_library(library_name, library_arguments)
        keyword_values = [[kw.name, kw.doc, u' | '.join(kw.arguments), lib[0]] for kw in keywords]
        self._insert_library_keywords(keyword_values)
        self._connection.commit()

    def _remove_old_versions(self, name, arguments):
        old_versions = self._connection.execute('select id from libraries where name = ? and arguments = ?', (name, arguments)).fetchall()
        self._connection.executemany('delete from keywords where library = ?', old_versions)
        self._connection.execute('delete from libraries where name = ? and arguments = ?', (name, arguments))

    def fetch_library_keywords(self, library_name, library_arguments):
        lib = self._fetch_lib(library_name, library_arguments)
        if lib is None:
            return []
        return [LibraryKeywordInfo(name, doc, lib[1], arguments.split(u' | '))
                for name, doc, arguments in
                self._connection.execute('select name, doc, arguments from keywords where library = ?', [lib[0]])]

    def library_exists(self, library_name, library_arguments):
        return self._fetch_lib(library_name, library_arguments) is not None

    def _insert_library(self, name, arguments):
        self._connection.execute('insert into libraries values (null, ?, ?, ?)', (name, arguments, time.time()))
        return self._fetch_lib(name, arguments)

    def _fetch_lib(self, name, arguments):
        t = self._connection.execute('select max(last_updated) from libraries where name = ? and arguments = ?', (name, arguments)).fetchone()[0]
        return self._connection.execute('select * from libraries where name = ? and arguments = ? and last_updated = ?', (name, arguments, t)).fetchone()

    def _insert_library_keywords(self, data):
        self._connection.executemany('insert into keywords values (?, ?, ?, ?)', data)
