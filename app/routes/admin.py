# approve events, manage users
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app.decorators import role_required

from app.utils import send_reminder_email
from app.models import Event, Registration, User, Attendance
from app import db
from app.models import Event

admin = Blueprint('admin', __name__)


# ---------------------------------------DASHBOARD----------------------------------------
@admin.route('/admin/dashboard')
@login_required
@role_required('admin')
def dashboard():
    from app.models import User, Registration, Event
    total_users = User.query.count() #How many users are on the platform(Users:120)
    total_events = Event.query.count() #Total events created (all statuses) (Events:21)
    total_regs = Registration.query.count() #Total participation across all events(Registration:400)

    # “Do I have work to do?
    pending_events = Event.query.filter_by(status='pending').count() #Events waiting for admin approval
    recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all() #sorts events by newest first(takes latest 5)

    # send data to template
    return render_template('admin/dashboard.html',
        total_users=total_users,
        total_events=total_events,
        total_regs=total_regs,
        pending_events=pending_events,
        recent_events=recent_events
    )


# -------------------------------------LISTING ALL EVENTS--------------------------------------
@admin.route('/admin/manage-events')
@login_required
@role_required('admin')
def manage_events():
    pending = Event.query.filter_by(status='pending').order_by(Event.created_at.desc()).all()
    all_events = Event.query.order_by(Event.created_at.desc()).all()
    return render_template('admin/manage_events.html', pending=pending, all_events=all_events) #Send data to template


# -------------------------------------APPROVE PENDING'S EVENTS--------------------------------------
@admin.route('/admin/approve-event/<int:event_id>', methods=['POST'])
@login_required
@role_required('admin')
def approve_event(event_id):
    event = Event.query.get_or_404(event_id) # if not found 404 error

    # prevents double approval
    if(event.status != 'pending'):
        flash('This event is already processed.', 'warning')
        return redirect(url_for('admin.manage_events'))

    event.status = 'approved' # approve the status
    db.session.commit() #writes to DB
    flash(f'"{event.title}" has been approved!', 'success')
    return redirect(url_for('admin.manage_events'))


# -----------------------------REJECT PENDING'S EVENTS------------------------------
@admin.route('/admin/reject-event/<int:event_id>', methods=['POST'])
@login_required
@role_required('admin')
def reject_event(event_id):
    event = Event.query.get_or_404(event_id)

    if event.status != 'pending':
        flash('This event is already processed.', 'warning')
        return redirect(url_for('admin.manage_events'))

    event.status = 'rejected'
    db.session.commit()
    flash(f'"{event.title}" has been rejected.', 'danger')
    return redirect(url_for('admin.manage_events'))


# ----------------------------------SEND REMINDER----------------------------

@admin.route('/admin/send-reminders/<int:event_id>', methods=['POST'])
@login_required
@role_required('admin')
def send_reminders(event_id):
    event = Event.query.get_or_404(event_id)
    registrations = Registration.query.filter_by(
        event_id=event_id,
        status='confirmed'
    ).all() # get all registered student, for this event(status = 'confirmed')

    count = 0 # how many email did we send?
    for reg in registrations:
        send_reminder_email(reg.user, event) #one email per student
        count += 1

    flash(f'Reminder emails sent to {count} students!', 'success')
    return redirect(url_for('admin.manage_events'))



# ---------------------------MANAGE USERS-------------------------------------
@admin.route('/admin/manage-users')
@login_required
@role_required('admin')
def manage_users():
    return '<h2>Manage Users — Coming Soon</h2>'


# ----------------------------------REPORTS---------------------------------
@admin.route('/admin/reports')
@login_required
@role_required('admin')
def reports():
    
    # user stats
    total_users = User.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_organisers = User.query.filter_by(role='organiser').count()

    # event stats
    total_events = Event.query.count()
    approved_events = Event.query.filter_by(status='approved').count()
    pending_events = Event.query.filter_by(status='pending').count()
    rejected_events = Event.query.filter_by(status='rejected').count()

    # registration stats
    total_regs = Registration.query.count()
    confirmed_regs = Registration.query.filter_by(status='confirmed').count()
    waitlist_regs = Registration.query.filter_by(status='waitlist').count()

    # attendance stats
    total_attended = Attendance.query.filter_by(is_present=True).count()
    attendance_rate = round((total_attended / confirmed_regs * 100), 1) if confirmed_regs > 0 else 0

    # top events by registration
    top_events = db.session.query(
        Event.title,
        db.func.count(Registration.id).label('reg_count')
    ).join(Registration, Event.id == Registration.event_id)\
     .filter(Event.status == 'approved')\
     .group_by(Event.id)\
     .order_by(db.func.count(Registration.id).desc())\
     .limit(5).all()


    return render_template('admin/reports.html',
        total_users=total_users,
        total_students=total_students,
        total_organisers=total_organisers,
        total_events=total_events,
        approved_events=approved_events,
        pending_events=pending_events,
        rejected_events=rejected_events,
        total_regs=total_regs,
        confirmed_regs=confirmed_regs,
        waitlist_regs=waitlist_regs,
        total_attended=total_attended,
        attendance_rate=attendance_rate,
        top_events=top_events
    )