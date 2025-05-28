from flask import render_template, request, jsonify
import json
from sqlalchemy import select
from MA_Scraper.app import db, website_name
from MA_Scraper.app.models import Users
from datetime import datetime
from MA_Scraper.app import cache_manager

def render_with_base(content_template, sidebar_html=None, title=None, main_content_class='', **variables):
    js_files = JSON(content_template)
    auto_title = Title(content_template)
    
    title = f"{title} - {website_name}" if title else auto_title
    # This is triggered when someone accesses a page through ajax (sidebar links all are intercepted and turned into ajax requests)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html_content = render_template(content_template, **variables, ajax=True)
        return jsonify({
            'html': html_content,
            'js_files': js_files,
            'title': title,
            'website_name': website_name,
            'sidebar': sidebar_html,
            'main_content_class': main_content_class
        })
    # Regular requests directly append the required javascript scripts as a parameter which is interpret by jinja.
    return render_template('base.html', content_template=content_template, **variables, js_files=js_files, page_title=title, website_name=website_name, main_content_class=main_content_class)

def JSON(attribute, path=rf'MA_Scraper/app/Javascript.json'):
        with open(path, 'r') as file:
            config = json.load(file)
        value = config.get(attribute)
        return value if value else None

def Title(content_template):
     content_name = f"{content_template[:-5].replace("_", " ").title()}"

     title = f"{content_name} - {website_name}"
     if content_name == 'Index':
        title = website_name
     return title

def liked_bands(current_user_id):
    liked_bands = db.session.scalars(select(Users.band_id).where(
    Users.user_id == current_user_id,Users.liked == True).distinct()).all()
    return liked_bands

def Like_bands(user_id, band_id, action):
    now = datetime.now().replace(microsecond=0)
    existing_preference = Users.query.filter_by(user_id=user_id, band_id=band_id).first()

    if existing_preference:
        if action == 'like':
            existing_preference.liked = True
            existing_preference.liked_date = now
        elif action == 'dislike':
            existing_preference.liked = False
            existing_preference.liked_date = now
        elif action == 'remind_me':
            if existing_preference.remind_me:
                existing_preference.remind_me = False
                existing_preference.remind_me_date = now
            else:
                existing_preference.remind_me = True
                existing_preference.remind_me_date = now
    else:
        if action == 'like':
            new_preference = Users(user_id=user_id, band_id=band_id, liked=True, remind_me=False, liked_date=now)
        elif action == 'dislike':
            new_preference = Users(user_id=user_id, band_id=band_id, liked=False, remind_me=False, liked_date=now)
        elif action == 'remind_me':
            new_preference = Users(user_id=user_id, band_id=band_id, liked=None, remind_me=True, remind_me_date=now)
        db.session.add(new_preference)

    db.session.commit()
    if action == 'remind_me':
        cache_manager.reset_cache('/ajax/remind')