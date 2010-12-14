import re

def is_variable(value):
    return match_variable(value)

def match_variable(value):
    return re.match('([\$\@]{(.*?)})=?', value)

def find_variable_basenames(value):
    return re.findall('\${(.+?)[^\s\w]+.*?}?', value)

def is_list_variable(value):
    return re.match('\@{.*}', value)