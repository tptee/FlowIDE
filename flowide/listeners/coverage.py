import sublime
import sublime_plugin

from ..cli import CLI, InvalidContext
from ..settings import find_flow_settings
from ..util import debounce, wait_for_load
from ..view import rowcol_to_region, display_unknown_error


class FlowCoverageListener(sublime_plugin.EventListener):
    def on_selection_modified_async(self, view):
        self.view = view
        sublime.set_timeout_async(
            lambda: self.run_coverage(view)
        )

    @wait_for_load
    @debounce
    def run_coverage(self, view):
        settings = find_flow_settings(view.window().project_data())
        if not settings.get('show_coverage'):
            return

        result = None
        try:
            result = CLI(view).coverage()
        except InvalidContext:
            view.erase_regions('flow_error')
            view.erase_regions('flow_uncovered')
        except Exception as e:
            display_unknown_error(self.view, e)

        if not result:
            return

        regions = []

        for line in result['expressions']['uncovered_locs']:
            start = line['start']
            end = line['end']
            row = int(start['line']) - 1
            col = int(start['column']) - 1
            endrow = int(end['line']) - 1
            endcol = int(end['column'])
            regions.append(
                rowcol_to_region(view, row, col, endcol, endrow)
            )

        view.add_regions(
            'flow_uncovered', regions, 'comment', '',
            sublime.DRAW_STIPPLED_UNDERLINE +
            sublime.DRAW_NO_FILL +
            sublime.DRAW_NO_OUTLINE
        )

        uncovered_count = result['expressions']['uncovered_count']
        covered_count_text = 'Flow coverage: {} line{} uncovered'.format(
            uncovered_count, '' if uncovered_count is 1 else 's'
        )
        view.set_status('flow_coverage', covered_count_text)
