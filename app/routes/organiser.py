# create events, check-in, manage
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.decorators import role_required
from app import db
from app.models import Event
from datetime import datetime, timezone
import os
from werkzeug.utils import secure_filename

organiser = Blueprint('organiser', __name__)

# allowed image extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    if '.' not in filename:
        return False
    extension = filename.split('.')[-1].lower()
    if extension in ALLOWED_EXTENSIONS:
        return True
    else:
        return False


# -----------------------------------DASHBOARD----------------------------------------
@organiser.route('/organiser/dashboard')
@login_required
@role_required('organiser')
def dashboard():
    return '<h2>Organiser Dashboard</h2>'


# -------------------------------CREATE EVENT----------------------------------------
@organiser.route('/organiser/create-event', methods=['GET', 'POST'])
@login_required
@role_required('organiser')
def create_event():
    if request.method=='POST':
        title = request.form.get('title','').strip() # return default value '' if data does not exits
        description = request.form.get('description','').strip()
        venue = request.form.get('venue','').strip()
        date_str = request.form.get('date')
        capacity = request.form.get('capacity')

        # basic validation
        if not title or not capacity or not venue or not date_str:
            flash('Please fill all required fields.', 'danger')
            return redirect(url_for('organiser.create_event'))
        
        #Convert capacity into int
        try:
            capacity = int(capacity)
            if capacity<1:
                raise ValueError
        except ValueError:
            flash('Capacity must be a positive number.', 'danger')
            return redirect(url_for('organiser.create_event'))
        
        # Parse date
        try:
            event_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M') #converts string into datetime
            event_date = event_date.replace(tzinfo=timezone.utc) #Adds timezone info (UTC)
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('organiser.create_event'))

        # Check date is in future
        if event_date <= datetime.now(timezone.utc):
            flash('Event date must be in the future.', 'danger')
            return redirect(url_for('organiser.create_event'))
        
        #Handle Poster Uploads
        poster_filename = None #default value, no file uploaded
        poster_file = request.files.get('poster') 
        if poster_file and poster_file.filename != '': #if file exists and filename is not empty
            if not allowed_file(poster_file.filename):
                flash('Only .jpg or .jpeg or .png images allowed', 'danger')
                return redirect(url_for('organiser.create_event'))

            # check file size max 2MB
            poster_file.seek(0, os.SEEK_END)  #go to end of file by jumping at the end directly
            file_size = poster_file.tell() #get size in bytes
            poster_file.seek(0)     #reset to start
            if file_size>2*1024*1024:
                flash('Image must be under 2MB.', 'danger')
                return redirect(url_for('organiser.create_event'))
            
            poster_filename = secure_filename(f"event_{current_user.id}_{poster_file.filename}")
            upload_path = os.path.join('app', 'static', 'uploads', poster_filename)

            os.makedirs(os.path.dirname(upload_path), exist_ok=True) # create folder if not exists

            poster_file.save(upload_path) 
        
        # Save event to database
        new_event = Event(title=title,
                          description=description,
                          venue=venue,
                          date=event_date,
                          capacity=capacity,
                          poster=poster_filename,
                          organiser_id=current_user.id,
                          status='pending'
                    )
        db.session.add(new_event)
        db.session.commit()

        flash('Event submitted for approval!', 'success')
        return redirect(url_for('organiser.my_events'))
    
    return render_template('organiser/create_event.html')


# -------------------------------LISTING ALL EVENTS------------------------------
@organiser.route('/organiser/my-events')
@login_required
@role_required('organiser')
def my_events():
    return '<h2>My Events - Coming Soon!</h2>'


# ----------------------------------ATTENDANCE CHECKIN------------------------------
@organiser.route('/organiser/checkin')
@login_required
@role_required('organiser')
def checkin():
    return '<h2>Check-in — Coming Soon</h2>'