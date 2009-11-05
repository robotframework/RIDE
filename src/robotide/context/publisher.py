from wx.lib.pubsub import Publisher as WxPublisher


class Publisher(object):

    def __init__(self):
        self._listeners = []
        self._wxpublisher = WxPublisher()

    def publish(self, event):
        self._wxpublisher.sendMessage(event.topic.lower(), event)

    def subscribe(self, listener, event):
        self._listeners.append(_ListenerWrapper(listener))
        self._wxpublisher.subscribe(self._listeners[-1], self._get_event(event))

    def _get_event(self, event):
        event = isinstance(event, basestring) and event or event.topic
        return event.lower()

    def unsubscribe(self, listener, event):
        self._wxpublisher.unsubscribe(self._find_wrapper(listener),
                                      self._get_event(event))

    def _find_wrapper(self, listener):
        for wrapper in self._listeners:
            if wrapper.listener == listener:
                self._listeners.remove(wrapper)
                return wrapper
        return None


class _ListenerWrapper(object):

    def __init__(self, listener):
        self.listener = listener

    def __call__(self, event):
        self.listener(event.data)
