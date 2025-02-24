from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()