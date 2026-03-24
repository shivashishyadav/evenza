# create events, check-in, manage
from flask import Blueprint, render_template
from flask_login import login_required

organiser = Blueprint('organiser', __name__)

@organiser.route('/organiser/dashboard')
@login_required
def dashboard():
    return '<h2>Organiser Dashboard</h2>'
    