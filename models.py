from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db  # Import db from extensions.py
from flask_jwt_extended import create_access_token

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)  # Added username field
    password_hash = db.Column(db.String(128))  # Store hashed passwords
    role = db.Column(db.String(20), default='customer')  # 'customer' or 'caterer'
    profile_img = db.Column(db.String(256))
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)
    google_id = db.Column(db.String(100))  # For Google login
    github_id = db.Column(db.String(100))  # For GitHub login
    facebook_id = db.Column(db.String(100))  # For Facebook login
    is_admin = db.Column(db.Boolean, default=False)  # Added is_admin field

    # Relationships
    meals = db.relationship('Meal', back_populates='caterer', lazy=True, cascade="all, delete-orphan")

    # Password hashing
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self):
        expires = timedelta(minutes=30)  # Token expires in 30 minutes
        return create_access_token(identity=self.email, expires_delta=expires)

    def __repr__(self):
        return f'<User {self.username} ({self.email})>'

class Meal(db.Model):
    __tablename__ = 'meals'  # Ensure table name is explicit
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    caterer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)  # Foreign Key to User

    caterer = db.relationship('User', back_populates='meals')  # Correct back_populates

    def __init__(self, name, price, image_url, caterer_id):
        self.name = name
        self.price = price
        self.image_url = image_url
        self.caterer_id = caterer_id

    def __repr__(self):
        return f'<Meal {self.name} - ${self.price}>'


class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'
    
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False)  # JWT ID (unique identifier for the token)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of when the token was revoked

    def __repr__(self):
        return f"<TokenBlocklist {self.jti}>"
