import os
import json
import sublime
import subprocess

from .util import find_flow_bin, find_flow_config, merge_dicts


def parse_cli_dependencies(view, add_magic_token=False):
    filename = view.file_name()
    flow_project_root = find_flow_config(filename)
    sublime_project_settings = view.window().project_data()
    binary = find_flow_bin(flow_project_root, sublime_project_settings)

    cursor_pos = view.sel()[0].begin()
    row, col = view.rowcol(cursor_pos)

    current_contents = view.substr(
        sublime.Region(0, view.size())
    )

    cursor_scope = view.scope_name(cursor_pos)

    if add_magic_token:
        current_lines = current_contents.splitlines()
        current_line = current_lines[row]
        tokenized_line = current_line[0:col] + 'AUTO332' + current_line[col:-1]
        current_lines[row] = tokenized_line
        current_contents = '\n'.join(current_lines)

    return {
        'bin': binary,
        'root': flow_project_root,
        'path': filename,
        'cursor_pos': cursor_pos,
        'cursor_scope': cursor_scope,
        'contents': current_contents,
        'row': row,
        'col': col
    }


class CLIInvocation:
    def __init__(self, **kwargs):
        self.bin = kwargs.get('bin')
        self.name = kwargs.get('name')

        # Args
        self._root = kwargs.get('root')
        self._path = kwargs.get('path')

        # Default args
        self._from_editor = kwargs.get('from_editor', 'nuclide')
        self._json = kwargs.get('json', True)
        self._retry_if_init = kwargs.get('retry_if_init', True)

        # Targets
        self.row = kwargs.get('row')
        self.col = kwargs.get('col')
        self.filename = kwargs.get('filename')
        self.contents = kwargs.get('contents')

    @property
    def root(self):
        return ['--root', self._root] \
            if self._root else None

    @root.setter
    def root(self, value):
        self._root = value

    @property
    def path(self):
        return ['--path', self._path] \
            if self._path else None

    @path.setter
    def path(self, value):
        self._path = value

    @property
    def from_editor(self):
        return ['--from', self._from_editor] \
            if self._from_editor else None

    @from_editor.setter
    def from_editor(self, value):
        self._from_editor = value

    @property
    def json(self):
        return ['--json'] if self._json else None

    @json.setter
    def json(self, value):
        self._json = value

    @property
    def retry_if_init(self):
        return [
            '--retry-if-init',
            'true' if self._retry_if_init else 'false'
        ]

    @retry_if_init.setter
    def retry_if_init(self, value):
        self._retry_if_init = value

    @property
    def args(self):
        properties = [
            self.from_editor,
            self.root,
            self.path,
            self.json,
            self.retry_if_init
        ]
        return [
            arg
            for args in properties
            if args is not None
            for arg in args
            if arg is not None
        ]

    @property
    def targets(self):
        targets = [
            self.row and str(self.row + 1) or None,
            self.col and str(self.col + 1) or None,
            self.filename
        ]

        return [
            target
            for target in targets
            if target is not None
        ]

    def serialize(self):
        return [self.bin, self.name] + self.args + self.targets


class InvalidContext(RuntimeError):
    pass


def extract_deps_from_view(add_magic_token=False):
    def wrapper(func):
        def wrapped(self, *args, **kwargs):
            kwargs['deps'] = parse_cli_dependencies(
                self.view,
                add_magic_token=add_magic_token
            )
            return func(self, *args, **kwargs)
        return wrapped
    return wrapper


def validate(func):
    def wrapper(self, *args, **kwargs):
        deps = kwargs['deps']
        if deps['root'] is '/':
            raise InvalidContext('No .flowconfig found.')

        if (
            '// @flow' not in deps['contents'] and
            '/* @flow */' not in deps['contents']
        ):
            raise InvalidContext('No @flow pragma present in contents.')

        if 'source.js' not in deps['cursor_scope']:
            raise InvalidContext('Contents are not Javascript.')

        kwargs['deps'] = deps
        return func(self, *args, **kwargs)
    return wrapper


class CLI:
    def __init__(self, view):
        self.view = view

    @extract_deps_from_view()
    @validate
    def get_def(self, **kwargs):
        deps = kwargs['deps']
        default_args = {
            'bin': deps['bin'],
            'name': 'get-def',
            'contents': deps['contents'],
            'root': deps['root'],
            'path': deps['path'],
            'row': deps['row'],
            'col': deps['col']
        }
        return self.call_cli(
            CLIInvocation(**merge_dicts(default_args, kwargs)),
        )

    @extract_deps_from_view()
    @validate
    def type_at_pos(self, **kwargs):
        deps = kwargs['deps']
        default_args = {
            'bin': deps['bin'],
            'name': 'type-at-pos',
            'contents': deps['contents'],
            'root': deps['root'],
            'path': deps['path'],
            'row': deps['row'],
            'col': deps['col']
        }
        return self.call_cli(
            CLIInvocation(**merge_dicts(default_args, kwargs)),
        )

    @extract_deps_from_view(add_magic_token=True)
    @validate
    def autocomplete(self, **kwargs):
        deps = kwargs['deps']
        default_args = {
            'bin': deps['bin'],
            'name': 'autocomplete',
            'contents': deps['contents'],
            'root': deps['root'],
            'retry_if_init': False,
            'filename': deps['path']
        }
        return self.call_cli(
            CLIInvocation(**merge_dicts(default_args, kwargs)),
        )

    @extract_deps_from_view()
    @validate
    def check_contents(self, **kwargs):
        deps = kwargs['deps']
        default_args = {
            'bin': deps['bin'],
            'name': 'check-contents',
            'contents': deps['contents'],
            'root': deps['root'],
            'retry_if_init': False,
            'filename': deps['path']
        }
        return self.call_cli(
            CLIInvocation(**merge_dicts(default_args, kwargs)),
        )

    @extract_deps_from_view()
    @validate
    def coverage(self, **kwargs):
        deps = kwargs['deps']
        default_args = {
            'bin': deps['bin'],
            'name': 'coverage',
            'contents': deps['contents'],
            'retry_if_init': False,
            'filename': deps['path']
        }
        return self.call_cli(
            CLIInvocation(**merge_dicts(default_args, kwargs)),
        )

    def call_cli(self, invocation):
        command = invocation.serialize()

        print(command)

        # Use a pipe for flow autocomplete's stdin
        read, write = os.pipe()
        os.write(write, str.encode(invocation.contents))
        os.close(write)

        # Make sure that we have the default place
        # flow is installed in our $PATH
        if '/usr/local/bin' not in os.environ['PATH']:
            os.environ['PATH'] += ':/usr/local/bin'

        try:
            output = subprocess.check_output(
                command,
                stderr=subprocess.STDOUT,
                stdin=read,
                shell=False
            )
            return json.loads(output.decode('utf-8'))
        except subprocess.CalledProcessError as e:
            try:
                return json.loads(e.output.decode('utf-8'))
            except:
                print(e.output)
                raise
        except Exception as e:
            print(e)
            raise
        finally:
            os.close(read)
