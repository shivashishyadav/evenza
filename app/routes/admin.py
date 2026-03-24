# approve events, manage users
from flask import Blueprint, render_template
from flask_login import login_required

admin = Blueprint('admin', __name__)

@admin.route('/admin/dashboard')
@login_required
def dashboard():
    return '<h2>Admin Dashboard</h2>'