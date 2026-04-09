# login, register, logout

# Creates a route group
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User
import random
from app.utils import send_otp_email
from datetime import datetime, timezone, timedelta
import os

auth = Blueprint('auth', __name__)

@auth.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'organiser':
            return redirect(url_for('organiser.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
        
    # NEW LOGIC: If NOT logged in, show the landing page instead of redirecting to login
    return render_template('home.html')


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

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        hashed_password = generate_password_hash(password=password)
        new_user = User(name=name,
            email=email,
            password=hashed_password, 
            role=role, 
            otp_code=otp, 
            is_verified=False,
            otp_created_at=datetime.now(timezone.utc),
            profile_pic='default_profile.png'
            )
        db.session.add(new_user) #stage changes
        db.session.commit() #save permanently   

        # 3. Send OTP Email
        send_otp_email(email, name, otp)

        flash('Success! Please enter the OTP sent to your email.', 'info')
        return redirect(url_for('auth.verify_otp', email=email))  
    
    return render_template('auth/register.html')

@auth.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    # If they are already logged in and verified, don't let them see otp verification page!
    if current_user.is_authenticated and current_user.is_verified:
        if current_user.role == 'organiser':
            return redirect(url_for('organiser.dashboard'))
        return redirect(url_for('student.dashboard'))

    email = request.args.get('email')
    if not email:
        return redirect(url_for('auth.register'))

    user = User.query.filter_by(email=email).first()

    if not user or user.is_verified:
        flash('Account already verified or link invalid.', 'info')
        return redirect(url_for('auth.login'))

    # 1. First, calculate the expiry time from the DB value
    expiry_time = user.otp_created_at + timedelta(minutes=1) # Changed to 10 mins, you had 1

    # 2. Fix the timezone issue (Naive vs Aware)
    if expiry_time.tzinfo is None:
        expiry_time = expiry_time.replace(tzinfo=timezone.utc)

    # 3. Get current time in UTC
    now = datetime.now(timezone.utc)
    
    remaining_seconds = int((expiry_time - now).total_seconds())

    if remaining_seconds <= 0:
        remaining_seconds = 0

    if request.method == 'POST':
        entered_otp = request.form.get('otp')

        if now > expiry_time:
            flash('OTP has expired. Please request a new one.', 'danger')
            return redirect(url_for('auth.verify_otp', email=email))

        if user.otp_code == entered_otp:
            user.is_verified = True
            user.otp_code = None  
            db.session.commit()
            
            login_user(user) 
            flash('Email verified! Welcome to Evenza.', 'success')
            
            if user.role == 'organiser':
                return redirect(url_for('organiser.dashboard'))
            return redirect(url_for('student.dashboard'))
        else:
            flash('Invalid OTP code.', 'danger')

    return render_template('auth/verify_otp.html', email=email, remaining_seconds=remaining_seconds)


@auth.route('/resend-otp/<email>')
def resend_otp(email):
    user = User.query.filter_by(email=email).first()
    
    if user and not user.is_verified:
        # Generate new OTP
        new_otp = str(random.randint(100000, 999999))
        user.otp_code = new_otp
        user.otp_created_at = datetime.now(timezone.utc) # If you add the field
        db.session.commit()
        
        # Send email
        send_otp_email(user.email, user.name, new_otp)
        flash('A new OTP has been sent to your email.', 'info')
    else:
        flash('Invalid request.', 'danger')
        
    return redirect(url_for('auth.verify_otp', email=email))


@auth.route('/login', methods=['GET','POST'])
def login():
    # 1. If already logged in, skip the login page
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

        # 2. Check if user exists and password is correct
        if(not user or not check_password_hash(user.password, password)):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        
        # Admin Auto-Verification
        if user.role == 'admin' and not user.is_verified:
            user.is_verified = True
            db.session.commit()
        
        # Verification Check for Non-Admins
        if user.role != 'admin' and not user.is_verified:
            flash('Your email is not verified yet. Please enter the OTP.', 'warning')
            return redirect(url_for('auth.verify_otp', email=user.email))
        

        # 4. Check if account is active (Admin toggle)
        # check if account is active(because it might be possible admin has been toggled(activated/deactivated) this user)
        if not user.is_active:
            flash('Your account has been deactivated. Contact admin.', 'danger')
            return redirect(url_for('auth.login'))

        # 5. All checks passed, log them in
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
    return redirect(url_for('auth.home'))


# --- USER PROFILE CRUD ---

# --- PUBLIC VIEW & SEARCH ---
@auth.route('/search/users')
@login_required
def search_users():
    query = request.args.get('q', '').lower().strip()
    if not query:
        return redirect(url_for('auth.home'))
    
    # Search for users by name (case-insensitive)
    # Filter out admins if you want to keep them private
    results = User.query.filter(
        User.name.ilike(f'%{query}%'),
        User.role != 'admin' 
    ).all()
    
    return render_template('auth/search_results.html', results=results, query=query)

@auth.route('/user/<int:user_id>')
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    # Check if the person viewing is the owner
    is_owner = (current_user.is_authenticated and current_user.id == user.id)
    return render_template('auth/public_profile.html', user=user, is_owner=is_owner)


from app.utils import allowed_file
from werkzeug.utils import secure_filename

@auth.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # 1. Update text info
        current_user.name = request.form.get('name', '').strip()
        current_user.bio = request.form.get('bio', '').strip()
        current_user.skills = request.form.get('skills', '').strip()

        # 2. Handle Image Upload
        file = request.files.get('profile_pic')
        if file and file.filename != '':
            # Use your file checker
            if not allowed_file(file.filename):
                flash('Invalid file type. Only jpg, jpeg, and png are allowed.', 'danger')
                return redirect(url_for('auth.edit_profile'))

            # Size check (2MB)
            file.seek(0, os.SEEK_END)
            if file.tell() > 2 * 1024 * 1024:
                flash('Image size must be less than 2MB.', 'danger')
                return redirect(url_for('auth.edit_profile'))
            file.seek(0)

            # Generate unique filename to avoid caching issues
            ext = file.filename.split('.')[-1].lower()
            unique_name = f"user_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
            filename = secure_filename(unique_name)

            # Pathing: app/static/uploads/profiles/
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'profiles')
            os.makedirs(upload_dir, exist_ok=True)
            
            upload_path = os.path.join(upload_dir, filename)
            file.save(upload_path)

            # Update the DB field
            current_user.profile_pic = filename

        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('auth.view_profile', user_id=current_user.id))

    return render_template('auth/edit_profile.html', user=current_user)

from app.utils import send_reset_otp_email # Add this to your imports

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email').lower().strip()
        user = User.query.filter_by(email=email).first()
        
        if user:
            otp = str(random.randint(100000, 999999))
            user.otp_code = otp
            user.otp_created_at = datetime.now(timezone.utc)
            db.session.commit()
            send_reset_otp_email(user.email, user.name, otp)
        
        # We flash success even if user doesn't exist for security (prevents email enumeration)
        flash('If this email exists, an OTP has been sent.', 'info')
        return redirect(url_for('auth.verify_reset_otp', email=email))
    
    return render_template('auth/forgot_password.html')

@auth.route('/verify-reset-otp', methods=['GET', 'POST'])
def verify_reset_otp():
    email = request.args.get('email')
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return redirect(url_for('auth.forgot_password'))

    # Calculate expiry (matching your verify_otp logic)
    expiry_time = user.otp_created_at + timedelta(minutes=1) 
    if expiry_time.tzinfo is None: expiry_time = expiry_time.replace(tzinfo=timezone.utc)
    remaining_seconds = int((expiry_time - datetime.now(timezone.utc)).total_seconds())

    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        if datetime.now(timezone.utc) > expiry_time:
            flash('OTP expired.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        if user.otp_code == entered_otp:
            # OTP is correct, send them to the actual reset page
            # We use a session flag so they can't skip to reset_password directly
            from flask import session
            session['reset_email'] = email
            return redirect(url_for('auth.reset_password'))
        else:
            flash('Invalid OTP.', 'danger')

    return render_template('auth/verify_otp.html', email=email, remaining_seconds=max(0, remaining_seconds))


@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    from flask import session
    email = session.get('reset_email')
    if not email:
        flash('Session expired. Start over.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if len(password) < 5:
            flash('Password too short.', 'danger')
            return render_template('auth/reset_password.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html')

        user = User.query.filter_by(email=email).first()
        user.password = generate_password_hash(password)
        user.otp_code = None # Clear the code
        db.session.commit()
        
        session.pop('reset_email', None) # Clear session
        flash('Password updated! You can now login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html')