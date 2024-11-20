from flask import render_template, request, jsonify
import json

def render_with_base(content_template, sidebar_html=None, title=None, **variables):
    js_files = JSON(content_template)
    auto_title = Title(content_template)
    title = f"{title} - Metallum Recommender" if title else auto_title
    # This is triggered when someone accesses a page through ajax (sidebar links all are intercepted and turned into ajax requests)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html_content = render_template(content_template, **variables, ajax=True)
        return jsonify({
            'html': html_content,
            'js_files': js_files,
            'title': title,
            'sidebar': sidebar_html,
            'target': f"/{content_template[:-5]}" if content_template[:-5] != '/index' else '/'
        })
    # Regular requests directly append the required javascript scripts as a parameter which is interpret by jinja.
    return render_template('base.html', content_template=content_template, **variables, js_files=js_files, page_title=title)

def JSON(attribute, path='app/Javascript.json'):
        with open(path, 'r') as file:
            config = json.load(file)
        value = config.get(attribute)
        return value if value else None

def Title(content_template):
     return f"{content_template[:-5].replace("_", " ").title()} - Metallum Recommender"