import os
import plugin_state
from threading import Timer
from .settings import find_flow_settings


def wait_for_load(func):
    def wrapper(*args, **kwargs):
        if not plugin_state.ready:
            return
        return func(*args, **kwargs)

    return wrapper


# Adapted from https://gist.github.com/walkermatt/2871026
def debounce(func):
    def debounced(self, *args, **kwargs):
        flow_settings = find_flow_settings(
            self.view.window().project_data()
        )
        debounce_ms = flow_settings.get('debounce_ms')

        def call_func():
            func(self, *args, **kwargs)
        try:
            debounced.timer.cancel()
        except(AttributeError):
            pass

        debounced.timer = Timer(debounce_ms / 1000, call_func)
        debounced.timer.start()
    return debounced


def merge_dicts(*dictionaries):
    result = {}
    for dictionary in dictionaries:
        result.update(dictionary)
    return result


def find_flow_config(filename):
    if not filename or filename is '/':
        return '/'

    potential_root = os.path.dirname(filename)
    if os.path.isfile(os.path.join(potential_root, '.flowconfig')):
        return potential_root

    return find_flow_config(potential_root)


def find_flow_bin(root_dir, project_data):
    flow_settings = find_flow_settings(project_data)
    if flow_settings.get('use_npm_flow'):
        npm_flow_bin = os.path.join(
            root_dir, 'node_modules/.bin/flow'
        )
        if os.path.isfile(npm_flow_bin):
            return npm_flow_bin

    flow_path = flow_settings.get('flow_path', 'flow')
    return flow_path
