from collections import namedtuple
import json
import os
import sublime
import sublime_plugin
import subprocess

CLIRequirements = namedtuple('CLIRequirements', [
    'filename', 'project_root', 'contents', 'row', 'col'
])


def find_flow_config(filename):
    if filename is "/":
        return "/"

    potential_root = os.path.dirname(filename)
    if os.path.isfile(os.path.join(potential_root, ".flowconfig")):
        return potential_root

    return find_flow_config(potential_root)


def build_snippet(name, params):
    snippet = name + '({})'
    paramText = ''

    for param in params:
        if not paramText:
            paramText += param["name"]
        else:
            paramText += ", " + param["name"]

    return snippet.format(paramText)


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
        tokenized_line = current_line[0:col] + "AUTO332" + current_line[col:-1]
        current_lines[row] = tokenized_line
        current_contents = '\n'.join(current_lines)

    return CLIRequirements(
        filename=filename,
        project_root=project_root,
        contents=current_contents,
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
        result = json.loads(output.decode("utf-8"))
        os.close(read)

        return result
    except subprocess.CalledProcessError as e:
        print(e.output)
        return None


class FlowGoToDefinition(sublime_plugin.TextCommand):
    def run(self, edit):
        deps = parse_cli_dependencies(self.view)

        result = call_flow_cli(deps.contents, [
            "flow", "get-def",
            "--from", "nuclide",
            "--root", deps.project_root,
            "--path", deps.filename,
            "--json",
            str(deps.row + 1), str(deps.col + 1)
        ])

        if result and result["path"]:
            sublime.active_window().open_file(
                result["path"] +
                ":" + str(result["line"]) +
                ":" + str(result["start"]),
                sublime.ENCODED_POSITION |
                sublime.TRANSIENT
            )


class FlowTypeHint(sublime_plugin.TextCommand):
    def run(self, edit):
        deps = parse_cli_dependencies(self.view)

        result = call_flow_cli(deps.contents, [
            "flow", "type-at-pos",
            "--from", "nuclide",
            "--root", deps.project_root,
            "--json",
            str(deps.row + 1), str(deps.col + 1)
        ])

        if result:
            self.view.show_popup(result["type"])


class FlowAutocomplete(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        if not view.match_selector(
            locations[0],
            "source.js - string - comment"
        ):
            return

        deps = parse_cli_dependencies(view, add_magic_token=True)

        result = call_flow_cli(deps.contents, [
            "flow", "autocomplete",
            "--from", "nuclide",
            "--root", deps.project_root,
            "--json"
        ])

        if result:
            return (
                [
                    (
                        match["name"] + "\t" + match["type"],
                        build_snippet(
                            match["name"],
                            match.get("func_details")["params"]
                        )
                        if match.get("func_details") else match["name"]
                    )
                    for match in result["result"]
                ],
                sublime.INHIBIT_WORD_COMPLETIONS |
                sublime.INHIBIT_EXPLICIT_COMPLETIONS
            )
