import sublime
import sublime_plugin

from ..cli import CLI, InvalidContext
from ..util import wait_for_load
from ..view import display_unknown_error


class FlowGoToDefinition(sublime_plugin.TextCommand):
    def run(self, edit):
        sublime.set_timeout_async(self.run_async)

    @wait_for_load
    def run_async(self):
        result = None
        try:
            result = CLI(self.view).get_def()
        except InvalidContext:
            print('Invalid context')
            pass
        except Exception as e:
            display_unknown_error(self.view, e)
            return

        print(result)
        if not result or not result.get('path'):
            return

        sublime.active_window().open_file(
            result['path'] +
            ':' + str(result['line']) +
            ':' + str(result['start']),
            sublime.ENCODED_POSITION |
            sublime.TRANSIENT
        )
