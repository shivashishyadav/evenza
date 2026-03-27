# browse events, register, dashboard
from flask import Blueprint, render_template
from flask_login import login_required
from app.decorators import role_required

student = Blueprint('student', __name__)

@student.route('/student/dashboard')
@login_required #Only logged-in users can logout
@role_required('student')
def dashboard():
    return '<h2>Student Dashboard</h2>'


@student.route('/student/my-events')
@login_required
@role_required('student')
def my_events():
    return '<h2>My Events - Coming Soon!</h2>'

@student.route('/student/my-certificates')
@login_required
@role_required('student')
def my_certificates():
    return '<h2>My Certificates - Coming Soon!</h2>'