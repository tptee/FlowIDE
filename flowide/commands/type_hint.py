import sublime
import sublime_plugin

from ..cli import CLI, InvalidContext
from ..util import wait_for_load
from ..view import display_unknown_error


class FlowTypeHint(sublime_plugin.TextCommand):
    def run(self, edit):
        sublime.set_timeout_async(self.run_async)

    @wait_for_load
    def run_async(self):
        result = None
        try:
            result = CLI(self.view).type_at_pos()
        except InvalidContext:
            pass
        except Exception as e:
            display_unknown_error(self.view, e)
            return

        if result:
            self.view.show_popup(result['type'])
