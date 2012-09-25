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
from Queue import Queue
import os
from threading import Thread
from robot.errors import DataError
from robotide.spec.librarydatabase import LibraryDatabase
from robotide.spec.libraryfetcher import _get_import_result_from_process
from robotide.spec.xmlreaders import _init_from_spec, _get_path

class LibraryManager(Thread):

    def __init__(self, database_name):
        self._database_name = database_name
        self._messages = Queue()
        Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        self._initiate_database_connection()
        while True:
            if not self._handle_message():
                break
        self._database.close()

    def _initiate_database_connection(self):
        self._database = LibraryDatabase(self._database_name)

    def _handle_message(self):
        message = self._messages.get()
        if not message:
            return False
        type = message[0]
        if type == 'fetch':
            self._handle_fetch_keywords_message(message)
        elif type == 'insert':
            self._handle_insert_keywords_message(message)
        return True

    def _handle_fetch_keywords_message(self, message):
        _, library_name, library_args, callback = message
        keywords = self._fetch_keywords(library_name, library_args)
        self._update_database_and_call_callback_if_needed((library_name, library_args), keywords, callback)

    def _fetch_keywords(self, library_name, library_args):
        try:
            path =_get_path(library_name.replace('/', os.sep), os.path.abspath('.'))
            return _get_import_result_from_process(path, library_args)
        except (ImportError, DataError):
            return _init_from_spec(library_name)

    def _handle_insert_keywords_message(self, message):
        _, library_name, library_args, result_queue = message
        keywords = self._fetch_keywords(library_name, library_args)
        self._insert(library_name, library_args, keywords, lambda result: result_queue.put(result))

    def _insert(self, library_name, library_args, keywords, callback):
        self._database.insert_library_keywords(library_name, library_args, keywords)
        self._call(callback, keywords)

    def _update_database_and_call_callback_if_needed(self, library_key, keywords, callback):
        db_keywords = self._database.fetch_library_keywords(*library_key)
        if not db_keywords or self._keywords_differ(keywords, db_keywords):
            self._insert(library_key[0], library_key[1], keywords, callback)
        else:
            self._database.update_library_timestamp(*library_key)

    def _call(self, callback, *args):
        try:
            callback(*args)
        except Exception:
            pass

    def fetch_keywords(self, library_name, library_args, callback):
        self._messages.put(('fetch', library_name, library_args, callback))

    def get_and_insert_keywords(self, library_name, library_args):
        result_queue = Queue()
        self._messages.put(('insert', library_name, library_args, result_queue))
        return result_queue.get()

    def stop(self):
        self._messages.put(False)

    def _keywords_differ(self, keywords1, keywords2):
        if keywords1 != keywords2 and None in (keywords1, keywords2):
            return True
        if len(keywords1) != len(keywords2):
            return True
        for k1, k2 in zip(keywords1, keywords2):
            if k1.name != k2.name:
                return True
            if k1.doc != k2.doc:
                return True
            if k1.arguments != k2.arguments:
                return True
            if k1.source != k2.source:
                return True
        return False
