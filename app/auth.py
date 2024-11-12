from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import users, db

# Create a blueprint for authentication routes
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.index'))  # Redirect to index after login
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
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
        new_user = users(
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
        return redirect(url_for('auth.login'))  # Redirect to login after successful registration

    return render_template('register.html')

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

    return render_template('profile.html')