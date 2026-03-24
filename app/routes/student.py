# browse events, register, dashboard
from flask import Blueprint, render_template
from flask_login import login_required

student = Blueprint('student', __name__)

@student.route('/student/dashboard')
@login_required #Only logged-in users can logout
def dashboard():
    return '<h2>Student Dashboard - Day 3</h2>'