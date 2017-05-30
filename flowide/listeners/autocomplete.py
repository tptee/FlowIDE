import sublime
import sublime_plugin

from ..cli import CLI, InvalidContext
from ..settings import find_flow_settings
from ..util import wait_for_load
from ..view import build_snippet, display_unknown_error


class FlowAutocompleteListener(sublime_plugin.EventListener):
    completions = None
    completions_ready = False

    # Used for async completions.
    def run_auto_complete(self):
        sublime.active_window().active_view().run_command('auto_complete', {
            'disable_auto_insert': True,
            'api_completions_only': False,
            'next_completion_if_showing': False,
            'auto_complete_commit_on_tab': True,
        })

    def on_query_completions(self, view, prefix, locations):
        # Return the pending completions and clear them
        if self.completions_ready and self.completions:
            self.completions_ready = False
            return self.completions

        sublime.set_timeout_async(
            lambda: self.on_query_completions_async(
                view, prefix, locations
            )
        )

    @wait_for_load
    def on_query_completions_async(self, view, prefix, locations):
        self.completions = None

        flow_settings = find_flow_settings(view.window().project_data())
        autocomplete_flags = sublime.INHIBIT_WORD_COMPLETIONS | \
            sublime.INHIBIT_EXPLICIT_COMPLETIONS
        if flow_settings.get('show_sublime_autocomplete_suggestions'):
            autocomplete_flags = 0

        result = None
        try:
            result = CLI(view).autocomplete()
        except InvalidContext:
            pass
        except Exception as e:
            display_unknown_error(self.view, e)

        if not result:
            return

        self.completions = (
            [
                (
                    # matching text
                    match['name'] + '\t' + match['type'],
                    # inserted text
                    build_snippet(
                        match['name'],
                        match.get('func_details')['params']
                    )
                    if (
                        match.get('func_details') and
                        not flow_settings.get('omit_function_parameters')
                    )
                    else match['name']
                )
                for match in result['result']
            ],
            autocomplete_flags
        )
        self.completions_ready = True
        sublime.active_window().active_view().run_command(
            'hide_auto_complete'
        )
        self.run_auto_complete()
