import sublime
import sublime_plugin

from ..cli import CLI, InvalidContext
from ..util import debounce, wait_for_load
from ..view import rowcol_to_region, display_unknown_error


class FlowCheckListener(sublime_plugin.EventListener):
    def on_selection_modified_async(self, view):
        self.view = view
        sublime.set_timeout_async(
            lambda: self.run_check(view)
        )

    @wait_for_load
    @debounce
    def run_check(self, view):
        result = None
        try:
            result = CLI(view).check_contents()
        except InvalidContext:
            view.erase_regions('flow_error')
            view.erase_regions('flow_uncovered')
        except Exception as e:
            display_unknown_error(self.view, e)

        if not result:
            return

        if result.get('passed'):
            view.erase_regions('flow_error')
            view.set_status('flow_error', 'Flow: no errors')
            return

        regions = []
        description_by_row = {}

        for error in result['errors']:
            rows = []
            description = ''

            operation = error.get('operation')
            if operation:
                row = int(operation['line']) - 1
                col = int(operation['start']) - 1
                endcol = int(operation['end'])
                regions.append(
                    rowcol_to_region(view, row, col, endcol)
                )
                rows.append(row)

            for message in error['message']:
                row = int(message['line']) - 1
                col = int(message['start']) - 1
                endcol = int(message['end'])
                regions.append(
                    rowcol_to_region(view, row, col, endcol)
                )
                rows.append(row)

                description += message['descr'] + ' '

            for row in rows:
                row_description = description_by_row.get(row)
                if not row_description:
                    description_by_row[row] = description
                if (
                    row_description and
                    description not in row_description
                ):
                    description_by_row[row] += '; ' + description

        view.add_regions(
            'flow_error', regions, 'scope.js', 'dot',
            sublime.DRAW_NO_FILL
        )

        error_count = len(result['errors'])
        error_count_text = 'Flow: {} error{}'.format(
            error_count, '' if error_count is 1 else 's'
        )

        cursor_pos = view.sel()[0].begin()
        row, _ = view.rowcol(cursor_pos)
        error_for_row = description_by_row.get(row)
        if error_for_row:
            view.set_status(
                'flow_error', error_count_text + ': ' + error_for_row
            )
        else:
            view.set_status('flow_error', error_count_text)
