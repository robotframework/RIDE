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

from robotide.lib.robot.utils import is_string


class CommentCache(object):

    def __init__(self):
        self._comments = []

    def add(self, comment):
        self._comments.append(comment)

    def consume_with(self, function):
        print(f"DEBUG: CommentCache enter consume_with {self._comments}")
        for comment in self._comments:
            function(comment)
        self.__init__()


class Comments(object):

    def __init__(self):
        self._comments = []

    def add(self, row):
        if row.comments:
            self._comments.extend(c.strip() for c in row.comments if c.strip())

    @property
    def value(self):
        return self._comments


class Comment(object):

    def __init__(self, comment_data):
        if comment_data and is_string(comment_data):
            comment_data = [comment_data] if comment_data else []
        self._comment = comment_data or []
        # print(f"DEBUG RFLib Comment input={comment_data} self._comment={self._comment}")

    def __len__(self):
        return len(self._comment)

    def as_list(self):
        if self._not_commented():
            if isinstance(self._comment, Comment):
                self._comment[0] = '# ' + self._comment._comment[0]
            else:
                self._comment[0] = '# ' + self._comment[0]
        if isinstance(self._comment, Comment):
            return self._comment._comment
        return self._comment

    def _not_commented(self):
        if isinstance(self._comment, Comment):
            return self._comment._comment[0] and self._comment._comment[0][0] != '#'
        if isinstance(self._comment, list):
            return self._comment and self._comment[0] and self._comment[0][0] != '#'
        return False
