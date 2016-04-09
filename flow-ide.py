from collections import namedtuple
import json
import os
import sublime
import sublime_plugin
import subprocess

CLIRequirements = namedtuple('CLIRequirements', [
    'filename', 'project_root', 'contents', 'cursor_pos', 'row', 'col'
])


def find_flow_config(filename):
    if filename is '/':
        return '/'

    potential_root = os.path.dirname(filename)
    if os.path.isfile(os.path.join(potential_root, '.flowconfig')):
        return potential_root

    return find_flow_config(potential_root)


def build_snippet(name, params):
    snippet = name + '({})'
    paramText = ''

    for param in params:
        if not paramText:
            paramText += param['name']
        else:
            paramText += ', ' + param['name']

    return snippet.format(paramText)


def rowcol_to_region(view, row, col, endcol):
    start = view.text_point(row, col)
    end = view.text_point(row, endcol)
    return sublime.Region(start, end)


def parse_cli_dependencies(view, **kwargs):
    filename = view.file_name()
    project_root = find_flow_config(filename)

    cursor_pos = view.sel()[0].begin()
    row, col = view.rowcol(cursor_pos)

    current_contents = view.substr(
        sublime.Region(0, view.size())
    )

    if kwargs.get('add_magic_token'):
        current_lines = current_contents.splitlines()
        current_line = current_lines[row]
        tokenized_line = current_line[0:col] + 'AUTO332' + current_line[col:-1]
        current_lines[row] = tokenized_line
        current_contents = '\n'.join(current_lines)

    return CLIRequirements(
        filename=filename,
        project_root=project_root,
        contents=current_contents,
        cursor_pos=cursor_pos,
        row=row, col=col
    )


def call_flow_cli(contents, command):
    # Use a pipe for flow autocomplete's stdin
    read, write = os.pipe()
    os.write(write, str.encode(contents))
    os.close(write)

    try:
        output = subprocess.check_output(
            command, stderr=subprocess.STDOUT, stdin=read
        )
        result = json.loads(output.decode('utf-8'))
        os.close(read)
        return result
    except subprocess.CalledProcessError as e:
        try:
            result = json.loads(e.output.decode('utf-8'))
            os.close(read)
            return result
        except:
            print(e.output)
            return None


class FlowGoToDefinition(sublime_plugin.TextCommand):
    def run(self, edit):
        sublime.set_timeout_async(self.run_async)

    def run_async(self):
        deps = parse_cli_dependencies(self.view)
        if deps.project_root is '/':
            return

        result = call_flow_cli(deps.contents, [
            'flow', 'get-def',
            '--from', 'nuclide',
            '--root', deps.project_root,
            '--path', deps.filename,
            '--json',
            str(deps.row + 1), str(deps.col + 1)
        ])

        if result and result['path']:
            sublime.active_window().open_file(
                result['path'] +
                ':' + str(result['line']) +
                ':' + str(result['start']),
                sublime.ENCODED_POSITION |
                sublime.TRANSIENT
            )


class FlowTypeHint(sublime_plugin.TextCommand):
    def run(self, edit):
        sublime.set_timeout_async(self.run_async)

    def run_async(self):
        deps = parse_cli_dependencies(self.view)
        if deps.project_root is '/':
            return

        result = call_flow_cli(deps.contents, [
            'flow', 'type-at-pos',
            '--from', 'nuclide',
            '--root', deps.project_root,
            '--json',
            str(deps.row + 1), str(deps.col + 1)
        ])

        if result:
            self.view.show_popup(result['type'])


class FlowListener(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        if not view.match_selector(
            locations[0],
            'source.js - string - comment'
        ):
            return

        deps = parse_cli_dependencies(view, add_magic_token=True)
        if deps.project_root is '/':
            return

        result = call_flow_cli(deps.contents, [
            'flow', 'autocomplete',
            '--from', 'nuclide',
            '--root', deps.project_root,
            '--json'
        ])

        if result:
            return (
                [
                    (
                        match['name'] + '\t' + match['type'],
                        build_snippet(
                            match['name'],
                            match.get('func_details')['params']
                        )
                        if match.get('func_details') else match['name']
                    )
                    for match in result['result']
                ],
                sublime.INHIBIT_WORD_COMPLETIONS |
                sublime.INHIBIT_EXPLICIT_COMPLETIONS
            )

    def on_selection_modified_async(self, view):
        deps = parse_cli_dependencies(view)
        if deps.project_root is '/':
            return

        scope = view.scope_name(deps.cursor_pos)
        if 'source.js' not in scope:
            return

        result = call_flow_cli(deps.contents, [
            'flow', 'check-contents',
            '--from', 'nuclide',
            '--json',
            deps.filename
        ])

        if result:
            if result['passed']:
                view.erase_regions('flow_error')
                view.set_status('flow_error', 'Flow: no errors')
                return

            for error in result['errors']:
                regions = []
                description = 'Flow: '

                operation = error.get('operation')
                if operation:
                    row = int(operation['line']) - 1
                    col = int(operation['start']) - 1
                    endcol = int(operation['end'])
                    regions.append(rowcol_to_region(view, row, col, endcol))

                for message in error['message']:
                    row = int(message['line']) - 1
                    col = int(message['start']) - 1
                    endcol = int(message['end'])
                    regions.append(rowcol_to_region(view, row, col, endcol))

                    description += message['descr']

                view.add_regions(
                    'flow_error', regions, 'scope.js', 'dot',
                    sublime.DRAW_NO_FILL
                )

                view.set_status('flow_error', description)
