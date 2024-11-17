from flask import render_template, request

def render_with_base(content_template, **variables):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template(content_template, **variables)
    return render_template('base.html', content_template=content_template, **variables)