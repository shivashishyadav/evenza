# App factory — initialises Flask, SQLAlchemy, Flask-Login and registers all blueprints in one place.

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

db = SQLAlchemy() # empty object
login_manager = LoginManager() # empty object
mail = Mail() # empty() object

def create_app():
    '''Function that builds app'''
    app = Flask(__name__) #Create Flask app instance
    app.config.from_object(Config) #Loads config from config.py

    db.init_app(app) #Connects Database (SQLAlchemy)

    login_manager.init_app(app) #Login system
    login_manager.login_view = 'auth.login' #If user not logged in, redirect to login page
    mail.init_app(app) #Attach the Mail system to this Flask app and load its configuration

    from app import models
    # THEN create tables
    with app.app_context():
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Import blueprints
    from app.routes.auth import auth
    from app.routes.student import student
    from app.routes.organiser import organiser
    from app.routes.admin import admin

    # Each blueprint is a module of routes
    app.register_blueprint(auth) #Activate routes inside auth.py
    app.register_blueprint(student)
    app.register_blueprint(organiser)
    app.register_blueprint(admin)

    # Error handlers: With our error handler, we control exactly what the user sees
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(401)
    def unauthorized(e):
        return render_template('errors/401.html'), 401
    

    return app
