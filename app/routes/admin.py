# approve events, manage users
from flask import Blueprint, render_template
from flask_login import login_required
from app.decorators import role_required

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
    return '<h2>Manage Events — Coming Soon</h2>'

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