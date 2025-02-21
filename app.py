from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
import os



# Initialize the app
app = Flask(__name__)

# Set the configuration (you can also store this in a separate config file)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/book_a_meal')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')  # Secret key for session management
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.mailtrap.io')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT', 587)
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'your_mailtrap_username')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'your_mailtrap_password')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'no-reply@bookameal.com')

# Initialize the database
db = SQLAlchemy(app)

# Initialize JWT Manager
jwt = JWTManager(app)

# Initialize Flask-Mail
mail = Mail(app)

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
