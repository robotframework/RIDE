import re


def is_variable(value):
    return is_scalar_variable(value) or is_list_variable(value)

def is_scalar_variable(value):
    return _match_scalar_variable(value)

def _match_scalar_variable(value):
    return re.match('^(\${.*?}) ?=?$', value.strip())

def is_list_variable(value):
    return _match_list_variable(value)

def _match_list_variable(value):
    return re.match('^(\@{.*?})(\ ?=?|\[\d*\])$', value.strip())

def get_variable(value):
    "Returns variables name without equal sign '=' and indexing '[2]' or None"
    match = is_variable(value)
    return match.groups()[0] if match else None

def get_variable_basename(value):
    "Return variable without extended variable syntax part"
    if is_list_variable(value):
        return get_variable(value)
    match = re.match('\${(.+?)[^\s\w]+.*?}?', value)
    if not match:
        return None
    return '${%s}' % (match.groups()[0].strip())

def find_variable_basenames(value):
    return [get_variable_basename(var) for var in re.findall('[\@\$]{.*?}', value)]

