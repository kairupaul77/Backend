from flask import Flask, jsonify, request
from extensions import db  # Import db from extensions.py
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_mail import Mail, Message
from flask_migrate import Migrate  # Add Flask-Migrate
import os
from threading import Thread

# Initialize the app
app = Flask(__name__)

# Set the configuration (you can also store this in a separate config file)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')  # Use SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587  # Usually 587 for TLS or 465 for SSL
app.config['MAIL_USE_TLS'] = True  # Set to False for SSL
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'faith.njau@student.moringaschool.com'
app.config['MAIL_PASSWORD'] = 'ifzh cbhn trgx ucel'
app.config['MAIL_DEFAULT_SENDER'] = 'faith.njau@student.moringaschool.com'

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

# Email sending function
def send_email_async(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Failed to send email: {str(e)}")

def send_email(subject, recipients, body):
    msg = Message(subject=subject, recipients=recipients, body=body)
    Thread(target=send_email_async, args=(app, msg)).start()

# User creation route
@app.route('/users', methods=['POST'])
def create_user():
    email = request.json.get('email')
    username = request.json.get('username')
    password = request.json.get('password')

    # Create new user
    new_user = User(email=email, username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    try:
        # Send confirmation email
        send_email(
            subject="Welcome to Book-A-Meal",
            recipients=[email],
            body="Thank you for registering with Book-A-Meal! We hope you enjoy our service."
        )
    except Exception as e:
        print(f"Error sending email: {str(e)}")  # Log the error
        return jsonify({"msg": "User registered successfully! But email failed to send."}), 201

    return jsonify({"msg": "User created successfully!"}), 201

# Error handling for 404
@app.errorhandler(404)
def page_not_found(e):
    return {"error": "Page not found"}, 404

# Error handling for 500
@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return {"error": "Internal server error"}, 500

# Test email route
@app.route('/test-email', methods=['GET'])
def test_email():
    msg = Message('Test Email', recipients=['recipient@example.com'])
    msg.body = 'This is a test email.'
    try:
        mail.send(msg)
        return "Email sent successfully!", 200
    except Exception as e:
        return f"Failed to send email: {str(e)}", 500

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
