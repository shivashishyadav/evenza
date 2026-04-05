# secret key, DB URI, mail config

# Load environment variables
import os
from dotenv import load_dotenv

load_dotenv() #read .env file

# Configuration class
# Used for:
# session security
# login cookies
class Config:
    # Use environment variable if it exists, otherwise use default value(dev)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///evenza.db' #Database connection
    SQLALCHEMY_TRACK_MODIFICATIONS = False #Saves memory
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB max upload

    # Flask-Mail Configuration
    MAIL_SERVER = 'smtp.gmail.com' # simple mail transfer protocol(used to send the emails)
    MAIL_PORT = 587 # this port is uses to send the mails securely, which door to use to talk to Gmail servers  
    MAIL_USE_TLS = True  # transport layer security(encrypt emails while sending and prevent credentials reading in between)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') 
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') #This should be a Gmail App Password, not our real password
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')
