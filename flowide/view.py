import sublime


def display_unknown_error(view, e):
    view.erase_regions('flow_error')
    view.erase_regions('flow_uncovered')
    view.set_status(
        'flow_error',
        'Unknown Flow error: ' + str(e)
    )


def build_snippet(name, params):
    snippet = name + '({})'
    paramText = ''

    for param in params:
        if not paramText:
            paramText += param['name']
        else:
            paramText += ', ' + param['name']

    return snippet.format(paramText)


def rowcol_to_region(view, row, col, endcol, endrow=None):
    if not endrow:
        endrow = row
    start = view.text_point(row, col)
    end = view.text_point(endrow, endcol)
    return sublime.Region(start, end)
