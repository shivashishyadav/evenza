from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app() #This initializes whole app(DB connected, config loaded, route registered)
 
with app.app_context(): # tells to flask, which app is running and which db to use
    existing = User.query.filter_by(email='admin@evenza.com').first() #Check if admin already exists
    if existing: #Prevents duplicate admin creation
        print('Admin already exists!')
    else:
        admin = User(
            name='Admin',
            email='admin@evenza.com',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print('Admin created successfully!')
        print('Email: admin@evenza.com')
        print('Password: admin123')