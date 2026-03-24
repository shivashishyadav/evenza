<!-- project description & screenshots -->
# Evenza 🎓
A full-stack college event management web app built with Flask.

## Features
- Student, Organiser, and Admin roles
- Event creation and registration
- QR code based check-in
- Email reminders
- PDF certificate generation

## Tech Stack
- Flask, SQLAlchemy, Flask-Login
- Bootstrap 5
- SQLite (dev) / PostgreSQL (prod)

## Setup Instructions

### 1. Clone the repo
git clone https://github.com/shivashishyadav/evenza.git
cd evenza

### 2. Create virtual environment
python -m venv myenv
myenv\Scripts\activate  # Windows

### 3. Install dependencies
pip install -r requirements.txt

### 4. Create .env file
SECRET_KEY=your-secret-key

### 5. Create database
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

### 6. Run the app
python run.py