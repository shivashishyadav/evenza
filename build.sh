#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created!')
"
python -c "
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import os

app = create_app()
with app.app_context():
    email = os.environ.get('ADMIN_EMAIL')
    password = os.environ.get('ADMIN_PASSWORD')

    print('ENV EMAIL:', email)
    print('ENV PASSWORD:', password)

    users = User.query.all()
    print('ALL USERS IN DB:')
    for u in users:
        print('User ->', u.email, '| role:', u.role)

    if not email or not password:
        print('ERROR: ADMIN_EMAIL and ADMIN_PASSWORD must be set!')
        exit(1)

    existing = User.query.filter_by(email=email).first()
    if existing:
        existing.password = generate_password_hash(password)
        db.session.commit()
        print('Admin password updated!')
    else:
        admin = User(
            name='Admin',
            email=email,
            password=generate_password_hash(password),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin created successfully!')
"