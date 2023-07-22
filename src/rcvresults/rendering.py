"""
Supports rendering Jinja2 templates.
"""


def format_int(value):
    # Add comma separators, and don't show a decimal point.
    return f'{value:,.0f}'


def format_percent(value):
    # Show 2 decimal places.
    percent = 100 * value
    return f'{percent:.2f}%'


def render_contest(template, results, path):
    candidates = results['candidates']
    html = template.render(results)
    path.write_text(html)
