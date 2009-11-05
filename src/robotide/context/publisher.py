from wx.lib.pubsub import Publisher as WxPublisher


class Publisher(object):

    def __init__(self):
        self._listeners = []
        self._wxpublisher = WxPublisher()

    def subscribe(self, listener, event):
        self._listeners.append(_ListenerWrapper(listener))
        self._wxpublisher.subscribe(self._listeners[-1], self._get_event(event))

    def _get_event(self, event):
        event = isinstance(event, basestring) and event or event.topic
        return event.lower()

    def unsubscribe(self, listener, event):
        self._wxpublisher.unsubscribe(self._find_listener(listener),
                                      self._get_event(event))

    def _find_listener(self, listener):
        for l in self._listeners:
            if l.listener == listener:
                self._listeners.remove(l)
                return l
        return None


class _ListenerWrapper(object):

    def __init__(self, listener):
        self.listener = listener

    def __call__(self, event):
        self.listener(event.data)
