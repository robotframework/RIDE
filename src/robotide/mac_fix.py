def only_once(f):
    _events = set()
    def new(obj, *args):
        id = args[0].Id
        if id in _events:
            return
        _events.add(id)
        return f(obj, *args)
    return new