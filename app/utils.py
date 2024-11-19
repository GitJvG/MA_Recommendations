from flask import render_template, request, jsonify
import json

def render_with_base(content_template, **variables):
    js_files = JSON(content_template)
    page_title = Title(content_template)
    # This is triggered when someone accesses a page through ajax (sidebar links all are intercepted and turned into ajax requests)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html_content = render_template(content_template, **variables, ajax=True)
        return jsonify({
            'html': html_content,
            'js_files': js_files,
            'title': page_title
        })
    # Regular requests directly append the required javascript scripts as a parameter which is interpret by jinja.
    return render_template('base.html', content_template=content_template, **variables, js_files = js_files, page_title=page_title)


def JSON(attribute, path='app/Javascript.json'):
        with open(path, 'r') as file:
            config = json.load(file)
        value = config.get(attribute)
        return value if value else None

def Title(content_template):
     return f"{content_template[:-5].replace("_", " ").title()} - Metallum Recommender`"