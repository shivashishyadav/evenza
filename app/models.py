# All database tables as Python classes — User, Event, Registration, Attendance, Certificate.

from app import db
from flask_login import UserMixin
from datetime import datetime, timezone
from sqlalchemy import CheckConstraint

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    __table_args__ = (CheckConstraint("role IN ('student', 'organiser', 'admin')", name='check_user_role'),)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student') # student, organiser, admin
    created_at = db.Column(db.DateTime(timezone=True), default=lambda:datetime.now(timezone.utc))

    def __repr__(self):
        return f'<User {self.email} {self.role}>'


class Event(db.Model):

    __tablename__ = 'event'

    __table_args__ = (CheckConstraint("status IN ('pending', 'approved', 'rejected')", name='check_event_status'),)

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    venue = db.Column(db.String(150), nullable=False)
    date = db.Column(db.DateTime(timezone=True), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    poster = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  #Controls approval flow: pending, approved, rejected
    organiser_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    organiser = db.relationship('User', backref='events', passive_deletes=True)

    def __repr__(self):
        return f'<Event {self.title}>'


class Registration(db.Model):
    '''Connect User and Event'''
    __tablename__ = 'registration'

    # A student can register for the same event multiple times and the database won't stop it, thats why add constrain
    __table_args__ = (
            db.UniqueConstraint('user_id', 'event_id', name='unique_registration'),
            CheckConstraint("status IN ('confirmed', 'waitlist', 'cancelled')", name='check_registration_status'),     
          )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.String(20), default='confirmed', nullable=False) # confirmed, waitlist cancelled
    registered_at = db.Column(db.DateTime(timezone=True), default=lambda:datetime.now(timezone.utc))

    user = db.relationship('User', backref='registrations', passive_deletes=True)
    event = db.relationship('Event', backref='registrations', passive_deletes=True)

    def __repr__(self):
        return f'<Registration user={self.user_id} event={self.event_id}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'



    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey('registration.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    is_present = db.Column(db.Boolean, default=False)
    checked_in_at = db.Column(db.DateTime(timezone=True), nullable=True)

    registration = db.relationship('Registration', backref='attendance', uselist=False, passive_deletes=True)

    def __repr__(self):
        return f'<Attendance reg={self.registration_id} present={self.is_present}>'
    

class Certificate(db.Model):
    __tablename__ = 'certificate'

    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.Integer, db.ForeignKey('registration.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    file_path = db.Column(db.String(300), nullable=False)
    issued_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    registration = db.relationship('Registration', backref='certificate', uselist=False, passive_deletes=True)

    def __repr__(self):
        return f'<Certificate reg={self.registration_id}>'