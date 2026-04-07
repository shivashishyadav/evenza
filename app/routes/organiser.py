# create events, check-in, manage
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app.decorators import role_required
from app import db
from app.models import Event, Registration, Attendance
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
    # Gets only events created by this organiser(newest first)
    events = Event.query.filter_by(organiser_id=current_user.id).order_by(Event.created_at.desc()).all()
    total = len(events) #Gets only events created by this organiser
    pending = sum(1 for e in events if e.status=='pending') #waiting for admin
    approved = sum(1 for e in events if e.status=='approved')
    rejected = sum(1 for e in events if e.status=='rejected')

    #registration count per event
    events_data = []
    for event in events:
        # cout confirmed registrations
        count = Registration.query.filter_by(event_id=event.id,status='confirmed').count()
        events_data.append((event, count))

    # send to templates
    return render_template('organiser/dashboard.html',
        events_data=events_data,
        total=total,
        pending=pending,
        approved=approved,
        rejected=rejected
    )


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
            # 1. Check Extension (Keep validation!)
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
            
            # 3. NEW: Robust Pathing Logic
            from flask import current_app
            ext = os.path.splitext(poster_file.filename)[1]
            # Use timestamp to prevent "File already exists" errors if user uploads same image twice
            unique_name = f"event_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
            poster_filename = secure_filename(unique_name)

            # Pointing correctly to app/static/uploads
            upload_path = os.path.join(current_app.root_path, 'static', 'uploads', poster_filename)
            
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
    events = Event.query.filter_by(
        organiser_id=current_user.id
        ).order_by(Event.created_at.desc()).all()

    events_data = []
    for event in events:
        confirmed_count = Registration.query.filter_by(
            event_id=event.id,
            status='confirmed').count()
        
        waitlist_count = Registration.query.filter_by(
            event_id=event.id,
            status='waitlist'
        ).count()

        seats_left = event.capacity - confirmed_count
        events_data.append((event, confirmed_count, waitlist_count, seats_left))

    return render_template('organiser/my_events.html', events_data=events_data)


# ----------------------------------ATTENDANCE CHECKIN------------------------------
@organiser.route('/organiser/checkin/<int:event_id>')
@login_required
@role_required('organiser')
def checkin(event_id):
    event = Event.query.get_or_404(event_id) #fetch event from Database, 404 if not found

    # make sure this event belongs to this organiser(prevents organiser from accessing someone else's event)
    if(event.organiser_id!=current_user.id):
        flash('You can only check-in your own events.', 'danger')
        return redirect(url_for('organiser.my_events'))
    
    # only approved events can allow to check-in
    if event.status != 'approved':
        flash('Only approved events can be checked in.', 'danger')
        return redirect(url_for('organiser.my_events'))

    # get all confirmed registrations for this event(only confirmed user can be checked in)
    registrations = Registration.query.filter_by(
        event_id=event_id,
        status='confirmed'
    ).all()

    # build attendance map - reg_id -> is_present
    attendance_map = {}
    for reg in registrations:
        att = Attendance.query.filter_by(registration_id=reg.id).first()
        attendance_map[reg.id] = att.is_present if att else False
    
    # sends data and render template
    return render_template('organiser/checkin.html',
        event=event,
        registrations=registrations,
        attendance_map=attendance_map
    )


# ─── API endpoint — called by JS when QR is scanned ──────────
# This is called by JavaScript when QR is scanned
@organiser.route('/organiser/api/checkin', methods=['POST'])
@login_required
@role_required('organiser')
def api_checkin():

    # get qr data
    data = request.get_json()
    qr_data = data.get('qr_data', '')

    # QR format: EVENZA-REG-{reg_id}-{user_id}-{event_id}
    try:
        parts = qr_data.split('-')
        # Prevent fake QR codes
        if parts[0] != 'EVENZA' or parts[1] != 'REG':
            raise ValueError
        reg_id = int(parts[2])
        user_id = int(parts[3])
        event_id = int(parts[4])
    except (ValueError, IndexError):
        return jsonify({'success': False, 'message': 'Invalid QR code!'})
    
     # fetch registration
    reg = Registration.query.get(reg_id)
    if not reg:
        return jsonify({'success': False, 'message': 'Registration not found!'})

    # verify it matches
    if reg.user_id != user_id or reg.event_id != event_id:
        return jsonify({'success': False, 'message': 'QR code mismatch!'})

    # check if already checked in(prevent duplicate scan)
    existing = Attendance.query.filter_by(registration_id=reg_id).first()
    if existing and existing.is_present:
        return jsonify({'success': False, 'message': f'{reg.user.name} already checked in!'})

    # mark attendance
    if existing:
        existing.is_present = True #mark attendance
        existing.checked_in_at = datetime.now(timezone.utc)
    else: #or create new
        attendance = Attendance(
            registration_id=reg_id,
            is_present=True,
            checked_in_at=datetime.now(timezone.utc)
        )
        db.session.add(attendance) 

    # save in database
    db.session.commit()

    # Sent back to frontend
    return jsonify({
        'success': True,
        'message': f'{reg.user.name} checked in successfully!',
        'student_name': reg.user.name,
        'event_title': reg.event.title
    })


# ----------------------------------Attendance Export as CSV------------------------------
from flask import Response #send custom data, directly return file content to browser

@organiser.route('/organiser/export-attendance/<int:event_id>')
@login_required
@role_required('organiser')
def export_attendance(event_id):
    ''' Fetch event -> Verify ownership -> Collect data -> Convert to CSV -> Download file '''

    # fetch or no found
    event = Event.query.get_or_404(event_id)

    # organiser can only export THEIR events
    if event.organiser_id != current_user.id:
        flash('You can only export your own events.', 'danger')
        return redirect(url_for('organiser.my_events'))

    registrations = Registration.query.filter_by(
        event_id=event_id,
        status='confirmed'
    ).all()

    # collect ALL data BEFORE leaving app context(collect everything early)
    rows = [] #This will store structured data for CSV
    for reg in registrations: #Check if user attended
        # fetch attendance: Check if user attended
        attendance = Attendance.query.filter_by(
            registration_id=reg.id
        ).first()

        is_present = 'Yes' if attendance and attendance.is_present else 'No' #Convert attendance to readable format(Yes/No)

        # 05 Apr 2026, 10:30 AM, else —
        checked_in_at = (
            attendance.checked_in_at.strftime('%d %b %Y, %I:%M %p')
            if attendance and attendance.checked_in_at else '—'
        )

        rows.append({
            'name': reg.user.name,
            'email': reg.user.email,
            'registered_at': reg.registered_at.strftime('%d %b %Y'),
            'status': reg.status,
            'is_present': is_present,
            'checked_in_at': checked_in_at
        })

    # now build CSV from already-collected data
    def generate():
        yield 'Name,Email,Registration Date,Status,Attended,Check-in Time\n' # first line of csv(column)
        for row in rows:
            yield f'"{row["name"]}","{row["email"]}","{row["registered_at"]}","{row["status"]}","{row["is_present"]}","{row["checked_in_at"]}"\n'

    filename = f"{event.title.replace(' ', '_')}_attendance.csv"

    return Response(
        generate(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={filename}'
        }
    ) #Don’t open a page — just download this file(so externally no url rendering like - /organiser/export-attendance/5)