import unittest
from robotide.namespace.suggesters import SuggestionSource, HistorySuggester

class TestSuggestionSources(unittest.TestCase):

    def test_suggestion_source_when_controller_and_row(self):
        suggestion_source = SuggestionSource(plugin=None, controller=self._controller_mock('foo'))
        suggestions = suggestion_source.get_suggestions('foo', 1)
        self.assertEqual(1, len(suggestions))
        self.assertEqual('foobar', suggestions[0].name)

    def test_suggestion_source_when_no_controller(self):
        suggestion_source = SuggestionSource(plugin=self._plugin_mock('bar'), controller=None)
        suggestions = suggestion_source.get_suggestions('foo', 1)
        self.assertEqual(1, len(suggestions))
        self.assertEqual('barfoo', suggestions[0].name)

    def test_history_suggester(self):
        suggestion_source = HistorySuggester()
        self.assertEqual([], suggestion_source.get_suggestions('f'))
        suggestion_source.store('foo')
        self.assertEqual('foo', suggestion_source.get_suggestions('f')[0].name)
        self.assertEqual([], suggestion_source.get_suggestions('b'))
        suggestion_source.store('bar')
        self.assertEqual('bar', suggestion_source.get_suggestions('b')[0].name)
        self.assertEqual('foo', suggestion_source.get_suggestions('f')[0].name)

    def _controller_mock(self, name):
        controller_mock = lambda:0
        controller_mock.get_local_namespace_for_row = lambda row:controller_mock
        suggestion = lambda:0
        suggestion.name = '%sbar' % name
        suggestion.description = None
        controller_mock.get_suggestions = lambda value: [suggestion]
        return controller_mock

    def _plugin_mock(self, name):
        mock = lambda:0
        suggestion = lambda:0
        suggestion.name = '%sfoo' % name
        suggestion.description = None
        mock.content_assist_values = lambda value:[suggestion]
        return mock


if __name__ == '__main__':
    unittest.main()
