import os
import json
import random
import string
from flask import Flask, jsonify, request, redirect, session
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_mail import Mail, Message
from flask_migrate import Migrate
from threading import Thread
from extensions import db
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from werkzeug.security import generate_password_hash
from models import User, Meal, Menu, Order, Notification, Cart, CartItem, TokenBlocklist
from Views.auth import auth_bp
from Views.user import user_bp
from Views.meal import meal_bp
from Views.menu import menu_bp
from Views.order import order_bp
from dotenv import load_dotenv
from flask_cors import CORS  # Import Flask-CORS

# Load environment variables
load_dotenv()

# Initialize the app
app = Flask(__name__)
# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173"]}})


# Flask app configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///app.db')  # Use SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587  # TLS port
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Add missing secret keys
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your_super_secret_key')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your_other_secret_key')

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
mail = Mail(app)

# Google OAuth Configuration
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
client_secrets_json = os.getenv("GOOGLE_CLIENT_SECRET_JSON")

if not client_secrets_json:
    raise ValueError("GOOGLE_CLIENT_SECRET_JSON is missing! Check your .env file.")

try:
    client_secrets_dict = json.loads(client_secrets_json)
except json.JSONDecodeError as e:
    raise ValueError(f"Error parsing GOOGLE_CLIENT_SECRET_JSON: {e}")

flow = Flow.from_client_config(
    client_secrets_dict,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="http://127.0.0.1:5000/google_login/callback"
)

# Helper function to generate a random password
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

# Google login callback route
@app.route("/authorize_google")
def authorize_google():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/google_login/callback")
def google_callback():
    try:
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        session['credentials'] = credentials_to_dict(credentials)

        user_info = get_user_info(credentials)
        user = User.query.filter_by(email=user_info['email']).first()
        
        if not user:
            random_password = generate_random_password()
            hashed_password = generate_password_hash(random_password)
            user = User(name=user_info['name'], email=user_info['email'], password=hashed_password)
            db.session.add(user)
            db.session.commit()
        
        session['user_info'] = user_info
        return redirect("http://127.0.0.1:5000/spaces")
    except Exception as e:
        return f"Error during Google callback: {str(e)}", 500

def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

def get_user_info(credentials):
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()
    return {
        'email': user_info['email'],
        'name': user_info['name'],
        'picture': user_info['picture']
    }

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
        return jsonify({"msg": "User registered successfully! Confirmation email sent."}), 201
    except Exception as e:
        print(f"Error sending email: {str(e)}")  # Log the error
        return jsonify({"msg": "User registered successfully, but confirmation email failed to send."}), 201

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

# Error handling for 404
@app.errorhandler(404)
def page_not_found(e):
    return {"error": "Page not found"}, 404

# Error handling for 500
@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return {"error": "Internal server error"}, 500

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
