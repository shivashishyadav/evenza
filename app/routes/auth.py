# login, register, logout

# Creates a route group
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User

auth = Blueprint('auth', __name__)

@auth.route('/')
def home():
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'organiser':
            return redirect(url_for('organiser.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    if request.method=='POST':
        name = request.form.get('name')
        email = request.form.get('email').lower().strip()
        password = request.form.get('password')
        role = request.form.get('role')

        # Prevent admin registration
        if role not in ['student', 'organiser']:
            role = 'student'

        # Basic validation
        if not name or not email or not password:
            flash('All fields are required', 'danger')
            return redirect(url_for('auth.register'))

        if len(password) < 5:
            flash('Password must be at least 5 characters', 'danger')
            return redirect(url_for('auth.register'))

        # check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered, Please login', 'danger') 
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password=password)
        new_user = User(name=name, email=email, password=hashed_password, role=role)
        db.session.add(new_user) #stage changes
        db.session.commit() #save permanently   

        flash('Account created! Please login', 'success')
        return redirect(url_for('auth.login'))  
    
    return render_template('auth/register.html')

@auth.route('/login', methods=['GET','POST'])
def login():
    # if already logged in, redirect to dashboard
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'organiser':
            return redirect(url_for('organiser.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    
    if request.method=='POST':
        email=request.form.get('email').lower().strip()
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if(not user or not check_password_hash(user.password, password)):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user) #session["user_id"] = user.id

        # Flask flash messages are stored in the session until they are displayed. So when we login -> flash is stored -> redirect to dashboard (stub page, no template) -> flash never displays -> logout -> redirect to login page -> NOW both the old welcome flash AND logout flash display together.
        # flash(f'Welcome Back, {user.name}!', 'success') 

        # redirect based on role
        if user.role=='admin':
            return redirect(url_for('admin.dashboard'))
        elif user.role=='organiser':
            return redirect(url_for('organiser.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    
    return render_template('auth/login.html')

@auth.route('/logout', methods=['GET','POST'])
@login_required #Only logged-in users can logout
def logout():
    logout_user() # clear session, session["user_id"] removed
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))