# create events, check-in, manage
from flask import Blueprint, render_template
from flask_login import login_required
from app.decorators import role_required

organiser = Blueprint('organiser', __name__)

@organiser.route('/organiser/dashboard')
@login_required
@role_required('organiser')
def dashboard():
    return '<h2>Organiser Dashboard</h2>'


@organiser.route('/organiser/create-event')
@login_required
@role_required('organiser')
def create_event():
    return '<h2>Create Event - Coming Soon!</h2>'


@organiser.route('/organiser/my-events')
@login_required
@role_required('organiser')
def my_events():
    return '<h2>My Events - Coming Soon!</h2>'


@organiser.route('/organiser/checkin')
@login_required
@role_required('organiser')
def checkin():
    return '<h2>Check-in — Coming Soon</h2>'