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
            flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_with_base('login.html')

@auth.route('/logout', methods=['GET'])
def logout():
    logout_user()
    sidebar_html = render_template('sidebar.html')
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        index_html = render_template('index.html')
        return jsonify({
            'success': True,
            'sidebar_html': sidebar_html,
            'main_content_html': index_html
        })
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get user inputs
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        
        # Additional fields
        Birthyear = request.form['Birthyear']
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
            Birthyear=Birthyear, 
            gender=gender, 
            nationality=nationality, 
            genre1=genre1, 
            genre2=genre2, 
            genre3=genre3
        )
        
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return render_with_base(('auth.login'))  # Redirect to login after successful registration

    return render_with_base('register.html')

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Fetch current user from session
        current_user.Birthyear = request.form['Birthyear']
        current_user.gender = request.form['gender']
        current_user.nationality = request.form['nationality']
        current_user.genre1 = request.form['genre1']
        current_user.genre2 = request.form['genre2']
        current_user.genre3 = request.form['genre3']

        # Ensure all genres are different
        if current_user.genre1 == current_user.genre2 or current_user.genre2 == current_user.genre3 or current_user.genre1 == current_user.genre3:
            flash('Please select three different genres.', 'error')
            return redirect(url_for('auth.profile'))

        # Commit the changes to the database
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('main.index'))

    return render_with_base('profile.html')