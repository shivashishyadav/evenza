# All database tables as Python classes — User, Event, Registration, Attendance, Certificate.

from app import db
from flask_login import UserMixin
from datetime import datetime, timezone

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student') # student, organiser, admin
    created_at = db.Column(db.DateTime(timezone=True), default=lambda:datetime.now(timezone.utc))

    def __repr__(self):
        return f'<User {self.email} {self.role}>'