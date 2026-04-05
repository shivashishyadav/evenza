# browse events, register, dashboard
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.decorators import role_required
from app.models import Event, Registration
from app import db

student = Blueprint('student', __name__)


# --------------------------DASHBOARD-----------------------------
@student.route('/student/dashboard')
@login_required #Only logged-in users can logout
@role_required('student')
def dashboard():
    regs = Registration.query.filter_by(user_id=current_user.id).all() #all registration of current user
    total = len(regs) # total number of events of current user
    confirmed = sum(1 for r in regs if r.status=='confirmed') #Count only those with status = confirmed
    waitlist = sum(1 for r in regs if r.status=='waitlist') #Events where user is not guaranteed a seat

    # upcoming events only
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    # Only events that haven’t happened yet, Ignore waitlist events
    upcoming = [r for r in regs if r.event.date>now and r.status=='confirmed']

    # Send data to template & return template
    return render_template('student/dashboard.html',
        regs=regs,
        total=total,
        confirmed=confirmed,
        waitlist=waitlist,
        upcoming=upcoming
    )


# --------------------------My Events-------------------------------
@student.route('/student/my-events')
@login_required
@role_required('student')
def my_events():    
    regs = Registration.query.filter_by(user_id=current_user.id).all()
    total = len(regs)
    confirmed = sum(1 for r in regs if r.status == 'confirmed')
    waitlist = sum(1 for r in regs if r.status == 'waitlist')
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    upcoming = [r for r in regs if r.event.date > now and r.status == 'confirmed']
    return render_template('student/dashboard.html',
        regs=regs,
        total=total,
        confirmed=confirmed,
        waitlist=waitlist,
        upcoming=upcoming
    )   


# ------------------------Events Listing--------------------------------------
@student.route('/student/events')
@login_required
@role_required('student')
def events():
    search = request.args.get('search', '')
    query = Event.query.filter_by(status='approved')

    if search:
        query = query.filter(Event.title.ilike(f"%{search}%"))
    events = query.order_by(Event.date.asc()).all()

    events_list = []

    for event in events:
        count = Registration.query.filter_by(
            event_id=event.id,
            status='confirmed'
        ).count()

        seats_left = event.capacity - count
        events_list.append((event, seats_left))

    return render_template('student/events.html', events=events_list)


# ------------------------------REGISTER-----------------------------------
@student.route('/student/register/<int:event_id>', methods=["POST"])
@login_required
@role_required('student')
def register(event_id):
    event = Event.query.get_or_404(event_id)

    # # only approved events
    if event.status != 'approved':
        flash('This event is not available for registration.', 'danger')
        return redirect(url_for('student.events'))
    
    # check already registered: prevent duplicate
    existing = Registration.query.filter_by(
        user_id=current_user.id,
        event_id=event_id
    ).first()

    if existing:
        flash('Already registered!', 'warning')
        return redirect(url_for('student.my_events'))
    
    # count confirmed registrations
    count = Registration.query.filter_by(
        event_id=event_id,
        status='confirmed'
    ).count()

    if count < event.capacity:
        status = 'confirmed'
        flash('Registered successfully!', 'success')
    else:
        status = 'waitlist'
        flash('Event full, added to waitlist', 'warning')
    
    reg = Registration( #reg.id=None
        user_id=current_user.id,
        event_id=event_id,
        status=status
    )

    db.session.add(reg) # Added to session, still reg.id=None, because SQLAlchemy hasn’t sent query to DB yet
 
    # It sends pending changes to DB WITHOUT committing
    db.session.flush()  #get reg.id before commit(if i dont use flush then reg.id=None, thats crash the code)
    # if we dont use flush, data string for qr generation is: EVENZA-REG-None-5-3(useless, lost uniqueness)

    # flush = "talk to DB, but don’t finalize"
    # commit = "final save"

    from app.utils import generate_qr, send_confirmation_email
    #generate qr code only for confirmed registration
    # Waitlist users don’t have guaranteed seat
    if status == 'confirmed': 
        qr_filename = generate_qr(reg.id, current_user.id, event_id)
        reg.qr_code = qr_filename #stores filename in DB, link registration to qr image

    db.session.commit()

    if status == 'confirmed':
        send_confirmation_email(current_user, event, qr_filename) # send mail
        flash('Registered successfully! Your QR code is ready.', 'success')
    else:
        flash('Event full — added to waitlist.', 'warning')

    return redirect(url_for('student.my_events'))


# ------------------------------CERTIFICATES------------------------------
@student.route('/student/my-certificates')
@login_required
@role_required('student')
def my_certificates():
    return '<h2>My Certificates - Coming Soon!</h2>'