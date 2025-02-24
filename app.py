from flask import Flask, jsonify, request
from extensions import db  # Import db from extensions.py
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_mail import Mail
from flask_migrate import Migrate  # Add Flask-Migrate
import os

# Initialize the app
app = Flask(__name__)

# Set the configuration (you can also store this in a separate config file)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')  # Use SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')  # Secret key for session management
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your_jwt_secret_key')  # JWT secret key
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.mailtrap.io')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT', 587)
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your_mailtrap_username')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your_mailtrap_password')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'no-reply@bookameal.com')

# Initialize the database
db.init_app(app)  # Initialize db with the app

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Initialize JWT Manager
jwt = JWTManager(app)

# Initialize Flask-Mail
mail = Mail(app)

# Import models after initializing db
from models import User, Meal, Menu, Order, Notification, Cart, CartItem, TokenBlocklist  # Import all your models

# Import blueprints
from Views.auth import auth_bp
from Views.user import user_bp
from Views.meal import meal_bp
from Views.menu import menu_bp
from Views.order import order_bp

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(meal_bp)
app.register_blueprint(menu_bp)
app.register_blueprint(order_bp)

# Home route
@app.route('/')
def home():
    return "Welcome to the Book-A-Meal API!"

# Login route
@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    # Check if the user exists and the password is correct
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"msg": "Bad username or password"}), 401

    # Create JWT token
    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token)

# Protected route
@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

# Handle errors (optional, for better error messages)
@app.errorhandler(404)
def page_not_found(e):
    return {"error": "Page not found"}, 404

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return {"error": "Internal server error"}, 500

# Run the app
if __name__ == "__main__":
    app.run(debug=True)