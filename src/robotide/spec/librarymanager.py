#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
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
import queue
from sqlite3 import OperationalError
from threading import Thread

import robotide.robotapi
from ..publish import RideLogException, RideLogMessage
from ..spec.librarydatabase import LibraryDatabase
from ..spec.libraryfetcher import get_import_result
from ..spec.xmlreaders import get_path, SpecInitializer


class LibraryManager(Thread):

    def __init__(self, database_name, spec_initializer=None):
        self._database_name = database_name
        self._database = None
        self._messages = queue.Queue()
        self._spec_initializer = spec_initializer or SpecInitializer()
        Thread.__init__(self)
        self.daemon = True

    def run(self):
        self._initiate_database_connection()
        while True:
            try:
                if not self._handle_message():
                    break
            except Exception as err:
                msg = 'Library import handling threw an unexpected exception'
                RideLogException(message=msg, exception=err, level='WARN').publish()
        self._database.close()

    def _initiate_database_connection(self):
        self._database = LibraryDatabase(self._database_name)

    def get_new_connection_to_library_database(self):
        library_database = LibraryDatabase(self._database_name)
        if self._database_name == ':memory:':
            # In memory database does not point to the right place.
            # this is here for unit tests.
            library_database.create_database()
        return library_database

    def _handle_message(self):
        message = self._messages.get()
        if not message:
            return False
        msg_type = message[0]
        if msg_type == 'fetch':
            self._handle_fetch_keywords_message(message)
        elif msg_type == 'insert':
            self._handle_insert_keywords_message(message)
        elif msg_type == 'create':
            self._database.create_database()
        return True

    def _handle_fetch_keywords_message(self, message):
        _, library_name, library_args, callback = message
        keywords = self._fetch_keywords(library_name, library_args)
        self._update_database_and_call_callback_if_needed(
            (library_name, library_args), keywords, callback)

    def _fetch_keywords(self, library_name, library_args):
        try:
            doc_paths = os.getenv('RIDE_DOC_PATH')
            collection = []
            path = get_path(library_name.replace('/', os.sep), os.path.abspath('.'))
            if path:
                results = get_import_result(path, library_args)
                if results:
                    return results
            if doc_paths:
                for p in doc_paths.split(','):
                    path = get_path(library_name.replace('/', os.sep), p.strip())
                    if path:
                        results = get_import_result(path, library_args)
                        if results:
                            collection.extend(results)
            if collection:
                return collection
            raise robotide.robotapi.DataError
        except Exception as err:
            try:
                print('FAILED', library_name, err)
            except IOError:
                pass
            kws = self._spec_initializer.init_from_spec(library_name)
            if not kws:
                msg = 'Importing test library "%s" failed' % library_name
                RideLogException(
                    message=msg, exception=err, level='WARN').publish()
            return kws

    def _handle_insert_keywords_message(self, message):
        _, library_name, library_args, result_queue = message
        keywords = self._fetch_keywords(library_name, library_args)
        self._insert(library_name, library_args, keywords,
                     lambda res: result_queue.put(res, timeout=3))

    def _insert(self, library_name, library_args, keywords, callback):
        self._database.insert_library_keywords(
            library_name, library_args, keywords or [])
        self._call(callback, keywords)

    def _update_database_and_call_callback_if_needed(
            self, library_key, keywords, callback):
        db_keywords = self._database.fetch_library_keywords(*library_key)
        try:
            if not db_keywords or self._keywords_differ(keywords, db_keywords):
                self._insert(
                    library_key[0], library_key[1], keywords, callback)
            else:
                self._database.update_library_timestamp(*library_key)
        except OperationalError:
            pass

    @staticmethod
    def _call(callback, *args):
        try:
            callback(*args)
        except Exception as err:
            msg = 'Library import callback threw an unexpected exception'
            RideLogException(message=msg, exception=err, level='WARN').publish()

    def fetch_keywords(self, library_name, library_args, callback):
        self._messages.put(('fetch', library_name, library_args, callback),
                           timeout=3)

    def get_and_insert_keywords(self, library_name, library_args):
        result_queue = queue.Queue(maxsize=1)
        self._messages.put(
            ('insert', library_name, library_args, result_queue), timeout=3)
        try:
            return result_queue.get(timeout=5)
        except queue.Empty as e:
            RideLogMessage(u'Failed to read keywords from library db: {}'
                           .format(str(e))).publish()
            return []

    def create_database(self):
        self._messages.put(('create',), timeout=3)

    def stop(self):
        self._messages.put(False, timeout=3)

    @staticmethod
    def _keywords_differ(keywords1, keywords2):
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
