from flask import render_template, request, jsonify
import json
from sqlalchemy import select
from MA_Scraper.app import website_name
from MA_Scraper.app.db import Session
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
    liked_bands = Session.scalars(select(Users.band_id).where(
    Users.user_id == current_user_id,Users.liked == True).distinct()).all()
    return liked_bands

def Like_bands(user_id, band_id, action):
    now = datetime.now().replace(microsecond=0)
    existing_preference = Session.query(Users).filter_by(user_id=user_id, band_id=band_id).first()

    if existing_preference:
        if action == 'like':
            existing_preference.liked_date = now
            existing_preference.liked = None if existing_preference.liked is True else True

        elif action == 'dislike':
            existing_preference.liked_date = now
            existing_preference.liked = None if existing_preference.liked is False else False

        elif action == 'remind_me':
            existing_preference.remind_me_date = now
            existing_preference.remind_me = False if existing_preference.remind_me is True else True
            
    else:
        if action == 'like':
            new_preference = Users(user_id=user_id, band_id=band_id, liked=True, remind_me=False, liked_date=now)
        elif action == 'dislike':
            new_preference = Users(user_id=user_id, band_id=band_id, liked=False, remind_me=False, liked_date=now)
        elif action == 'remind_me':
            new_preference = Users(user_id=user_id, band_id=band_id, liked=None, remind_me=True, remind_me_date=now)
        Session.add(new_preference)

    current_liked_state = existing_preference.liked if existing_preference else (new_preference.liked if 'new_preference' in locals() else None)
    current_remind_me_state = existing_preference.remind_me if existing_preference else (new_preference.remind_me if 'new_preference' in locals() else False)

    Session.commit()
    if action == 'remind_me':
        cache_manager.reset_cache('/ajax/remind')
    if action == 'dislike' or action == 'like':
        cache_manager.reset_cache('/ajax/recommended_albums')

    return current_liked_state, current_remind_me_state