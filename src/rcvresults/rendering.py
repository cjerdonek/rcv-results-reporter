"""
Supports rendering Jinja2 templates.
"""

def render_contest(template, results, path):
    candidates = results['candidates']
    html = template.render(results)
    path.write_text(html)
