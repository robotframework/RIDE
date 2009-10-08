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

def Keyword(kwdata):
    if kwdata.type == 'generated':
        return GeneratedKeyword(kwdata)
    if kwdata.type == 'set':
        return SetKeyword(kwdata)
    if kwdata.type == 'repeat':
        return RepeatKeyword(kwdata)
    if kwdata.type == 'for':
        ret = [ForKeyword(kwdata)]
        for kw in kwdata.keywords:
            ret.append(ForItemKeyword(kw))
        return ret
    if kwdata.type == 'parallel':
        ret = [ParallelKeyword(kwdata)]
        for kw in kwdata.keywords:
            ret.append(ForItemKeyword(kw))
        return ret
    return BaseKeyword(kwdata)
    
        
class BaseKeyword(object):
    
    def __init__(self, kwdata):
        self.name = kwdata.name
        self.doc = kwdata.doc
        self.args = kwdata.args
        
    def get_display_value(self):
        return [self.name] + self.args


class SetKeyword(BaseKeyword):
    
    def __init__(self, kwdata):
        BaseKeyword.__init__(self, kwdata)
        self.scalar_vars = kwdata.scalar_vars
        self.list_var = kwdata.list_var
        
    def get_display_value(self):
        variables = self.scalar_vars[:]
        if self.list_var is not None:
            variables.append(self.list_var)
        variables[-1] += ' ='
        return variables + [self.name] + self.args


class RepeatKeyword(BaseKeyword):
    
    def __init__(self, kwdata):
        BaseKeyword.__init__(self, kwdata)
        self.repeat = kwdata.repeat
        
    def get_display_value(self):
        return [str(self.repeat) + ' x'] + [self.name] + self.args    
    
    
class ForKeyword(BaseKeyword):
    def __init__(self, kwdata):
        BaseKeyword.__init__(self, kwdata)
        self.vars = kwdata.vars
        self.items = kwdata.items
        self.range = kwdata.range
        
    def get_display_value(self):
        in_token = self.range and 'IN RANGE' or 'IN'
        return [':FOR'] + self.vars + [in_token] + self.items


class ForItemKeyword(BaseKeyword):
    
    def __init__(self, kwdata):
        self._keyword = Keyword(kwdata) 
    
    def get_display_value(self):
        return [''] + self._keyword.get_display_value() 


class ParallelKeyword(BaseKeyword):

    def get_display_value(self):
        return [':PARALLEL']


class GeneratedKeyword(object):
    
    def __init__(self, data):
        self.data = data.data
        
    def get_display_value(self):
        return self.data


class KeywordData(object):
    
    def __init__(self, data):
        self.type = 'generated'
        self.data= data
