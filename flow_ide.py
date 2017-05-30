import plugin_state

from .flowide.commands.go_to_definition import *  # noqa
from .flowide.commands.type_hint import *  # noqa
from .flowide.listeners.autocomplete import *  # noqa
from .flowide.listeners.check import *  # noqa
from .flowide.listeners.coverage import *  # noqa


def plugin_loaded():
    plugin_state.ready = True
