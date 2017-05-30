import sublime


def get_setting(settings, project_data, key):
    if not project_data or not project_data.get('FlowIDE'):
        return settings.get(key)

    project_flow_ide_settings = project_data.get('FlowIDE')
    if project_flow_ide_settings.get(key) is not None:
        return project_flow_ide_settings.get(key)

    return settings.get(key)


def find_flow_settings(project_data):
    settings = sublime.load_settings('FlowIDE.sublime-settings')

    flow_settings = {}
    flow_settings['use_npm_flow'] = get_setting(
        settings,
        project_data,
        'use_npm_flow'
    )
    flow_settings['flow_path'] = get_setting(
        settings,
        project_data,
        'flow_path'
    )
    flow_settings['omit_function_parameters'] = get_setting(
        settings,
        project_data,
        'omit_function_parameters'
    )
    flow_settings['show_sublime_autocomplete_suggestions'] = get_setting(
        settings,
        project_data,
        'show_sublime_autocomplete_suggestions'
    )
    flow_settings['debounce_ms'] = get_setting(
        settings,
        project_data,
        'debounce_ms'
    )

    return flow_settings
