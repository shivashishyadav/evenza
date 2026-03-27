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