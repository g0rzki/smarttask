from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Model reprezentujący użytkownika
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    tasks = db.relationship('Task', backref='owner', lazy=True)

    # Funkcja do ustawiania hasła (generowanie hasha)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Funkcja do sprawdzania poprawności hasła
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Model reprezentujący zadanie
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    priority = db.Column(db.String(10), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    is_completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
