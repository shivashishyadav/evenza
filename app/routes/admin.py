# approve events, manage users
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from app.decorators import role_required

from app import db
from app.models import Event

admin = Blueprint('admin', __name__)

@admin.route('/admin/dashboard')
@login_required
@role_required('admin')
def dashboard():
    return '<h2>Admin Dashboard</h2>'

@admin.route('/admin/manage-events')
@login_required
@role_required('admin')
def manage_events():
    pending = Event.query.filter_by(status='pending').order_by(Event.created_at.desc()).all()
    all_events = Event.query.order_by(Event.created_at.desc()).all()
    return render_template('admin/manage_events.html', pending=pending, all_events=all_events) #Send data to template


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

@admin.route('/admin/manage-users')
@login_required
@role_required('admin')
def manage_users():
    return '<h2>Manage Users — Coming Soon</h2>'

@admin.route('/admin/reports')
@login_required
@role_required('admin')
def reports():
    return '<h2>Reports — Coming Soon</h2>'