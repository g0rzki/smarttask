import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

# Inicjalizacja bazy danych i logowania
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    load_dotenv() # Wczytanie zmiennych środowiskowych z .env

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') # Klucz sesji
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') # URL bazy danych
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Wyłączenie śledzenia zmian (oszczędność zasobów)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login' # Strona logowania

    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all() # Utworzenie tabel, jeśli nie istnieją
        from app.seeder import seed_db
        seed_db() # Utworzenie seederów, jeśli baza jest pusta

    return app
