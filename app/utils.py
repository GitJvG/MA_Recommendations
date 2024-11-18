from flask import render_template, request
import json

def render_with_base(content_template, **variables):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template(content_template, **variables, ajax=True)
    return render_template('base.html', content_template=content_template, **variables, js_files=JSON(content_template))

def JSON(attribute, path='app/Javascript.json'):
        with open(path, 'r') as file:
            config = json.load(file)
        value = config.get(attribute)
        return value if value else None
