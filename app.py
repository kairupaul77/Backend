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
from models import User, Meal, Order, Menu, Notification, TokenBlocklist
from Views.auth import auth_bp
from Views.user import user_bp
from Views.meal import meal_bp
from Views.menu import menu_bp
from Views.order import order_bp
from Views.notifications import notifications_bp

from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Allow specific origins and methods (including PUT and DELETE)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://localhost:5174", "https://pafaan-frontend.vercel.app"],
                             "supports_credentials": True,
                             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                             "allow_headers": ["Content-Type", "Authorization"]}})

@app.after_request
def add_headers(response):
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173" 
    response.headers["Access-Control-Allow-Origin"] ="https://pafaan-frontend.vercel.app"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# Flask app configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'postgresql://appdb_4ib8_user:yHGJjbJ4dATfTEA4W3uVg29rizkJuKhe@dpg-cv4biclds78s73dsevvg-a.oregon-postgres.render.com/appdb_4ib8'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your_super_secret_key')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your_other_secret_key')

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 9000
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 86400

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

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(meal_bp)
app.register_blueprint(menu_bp)
app.register_blueprint(order_bp)
app.register_blueprint(notifications_bp)

# Home route
@app.route('/')
def home():
    return "Welcome to the Book-A-Meal API!"



# Run the app
if __name__ == "__main__":
    app.run(debug=True)
