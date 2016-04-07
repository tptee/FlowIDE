import json
import os
import sublime
import sublime_plugin
import subprocess


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


class FlowAutocompleteListener(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        filename = view.file_name()
        current_contents = view.substr(sublime.Region(0, view.size()))
        project_root = find_flow_config(filename)

        cursor_pos = view.sel()[0].begin()
        row, col = view.rowcol(cursor_pos)

        current_lines = current_contents.splitlines()
        current_line = current_lines[row]
        tokenized_line = current_line[0:col] + "AUTO332" + current_line[col:-1]
        current_lines[row] = tokenized_line
        processed_lines = '\n'.join(current_lines)

        # Use a pipe for flow autocomplete's stdin
        read, write = os.pipe()
        os.write(write, str.encode(processed_lines))
        os.close(write)

        output = subprocess.check_output(
            [
                "flow", "autocomplete",
                "--from", "nuclide",
                "--root", project_root,
                "--json"
            ],
            stdin=read
        )
        result = json.loads(output.decode("utf-8"))["result"]
        os.close(read)

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
                for match in result
            ],
            sublime.INHIBIT_WORD_COMPLETIONS |
            sublime.INHIBIT_EXPLICIT_COMPLETIONS
        )
