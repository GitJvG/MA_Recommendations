from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import user, db
from app.utils import render_with_base
# Create a blueprint for authentication routes
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        queried_user = user.query.filter_by(username=username).first()  # Ensure 'User' is correctly imported

        if queried_user and check_password_hash(queried_user.password, password):
            login_user(queried_user)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                sidebar_html = render_template('sidebar.html')
                return jsonify({'success': True, 'sidebar_html': sidebar_html, 'redirect_url': url_for('main.index')})
            else:
                return redirect(url_for('main.index'))
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Invalid username or password'}), 401

    return render_with_base('login.html')

@auth.route('/logout', methods=['GET'])
def logout():
    logout_user()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        sidebar_html = render_template('sidebar.html')
        return render_with_base('index.html', sidebar_html=sidebar_html)
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get user inputs
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        
        # Additional fields
        birthyear = request.form['birthyear']
        gender = request.form['gender']
        nationality = request.form['nationality']
        
        # Capture genres from three separate dropdowns
        genre1 = request.form['genre1']
        genre2 = request.form['genre2']
        genre3 = request.form['genre3']

        # Ensure all three genres are different
        if genre1 == genre2 or genre2 == genre3 or genre1 == genre3:
            flash('Please select three different genres.', 'error')
            return redirect(url_for('auth.register'))  # Redirect back to the registration form if validation fails

        # Create new user entry
        new_user = user(
            username=username, 
            email=email, 
            password=password, 
            birthyear=birthyear, 
            gender=gender, 
            nationality=nationality, 
            genre1=genre1, 
            genre2=genre2, 
            genre3=genre3
        )
        
        db.session.add(new_user)
        db.session.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'redirect_url': url_for('auth.login')})
        else:
            return redirect(url_for('auth.login'))

    return render_with_base('register.html')

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Fetch current user from session
        current_user.birthyear = request.form['birthyear']
        current_user.gender = request.form['gender']
        current_user.nationality = request.form['nationality']
        current_user.genre1 = request.form['genre1']
        current_user.genre2 = request.form['genre2']
        current_user.genre3 = request.form['genre3']

        # Ensure all genres are different
        if current_user.genre1 == current_user.genre2 or current_user.genre2 == current_user.genre3 or current_user.genre1 == current_user.genre3:
            return jsonify({'error': 'Please select three different genres'})

        # Commit the changes to the database
        db.session.commit()
        return jsonify({'success': True, 'pop_up': 'Profile updated successfully.'})

    return render_with_base('profile.html', user=current_user)
