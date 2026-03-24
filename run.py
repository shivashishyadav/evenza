#  entry point — python run.py

from app import create_app

app = create_app() #Calls create_app() from app/__init__.py

if __name__ == '__main__':
    app.run(debug=True)