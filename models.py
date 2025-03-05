from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db  # Import db from extensions.py
from flask_jwt_extended import create_access_token
from sqlalchemy import DateTime, Column, Date  # Add Date here

# Association table for many-to-many relationship between Menu and Meal
menu_meals = db.Table(
    'menu_meals',
    db.Column('menu_id', db.Integer, db.ForeignKey('menus.id', ondelete="CASCADE"), primary_key=True),
    db.Column('meal_id', db.Integer, db.ForeignKey('meals.id', ondelete="CASCADE"), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)  # Use this as the full name
    password_hash = db.Column(db.String(512))
    role = db.Column(db.String(20), default='customer')
    profile_img = db.Column(db.String(256), default='default_profile_img.png')
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    github_id = db.Column(db.String(100), unique=True, nullable=True)
    facebook_id = db.Column(db.String(100), unique=True, nullable=True)

    meals = db.relationship('Meal', back_populates='caterer', lazy=True, cascade="all, delete-orphan")
    orders = db.relationship('Order', back_populates='user', cascade="all, delete-orphan")
    notifications = db.relationship('Notification', back_populates='user', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self):
        expires = timedelta(minutes=30)
        return create_access_token(identity=self.id, expires_delta=expires)

    def __repr__(self):
        return f'<User {self.username} ({self.email})>'

    # Use 'username' as the full name directly
    @property
    def full_name(self):
        return self.username

class Meal(db.Model):
    __tablename__ = 'meals'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), default='default_meal_img.png')
    caterer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

    caterer = db.relationship('User', back_populates='meals')
    menus = db.relationship('Menu', secondary=menu_meals, back_populates='meals')

    def __repr__(self):
        return f'<Meal {self.name} - ${self.price}>'

class Menu(db.Model):
    __tablename__ = 'menus'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    date = db.Column(Date, nullable=False, unique=True, index=True)

    meals = db.relationship('Meal', secondary=menu_meals, back_populates='menus')
    orders = db.relationship('Order', backref='menu', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Menu {self.name} - {self.date}>'

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.id', ondelete="CASCADE"), nullable=True)
    menu_id = db.Column(db.Integer, db.ForeignKey('menus.id', ondelete="CASCADE"), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # Set a default value
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    payment_status = db.Column(db.Boolean, default=False)  # Payment status
    user = db.relationship('User', back_populates='orders')
    meal = db.relationship('Meal', backref='orders')

    def update_order(self, new_meal_id, new_quantity):
        """Allows the user to change their meal choice."""
        self.meal_id = new_meal_id
        self.quantity = new_quantity
        self.total_price = self.meal.price * new_quantity
        db.session.commit()

    @staticmethod
    def get_daily_revenue(date):
        """Calculates total revenue for a specific day."""
        total_revenue = db.session.query(db.func.sum(Order.total_price))\
            .join(Menu, Order.menu_id == Menu.id)\
            .filter(Menu.date == date).scalar()
        return total_revenue or 0

    @property
    def customer_name(self):
        """Returns the username of the customer."""
        return self.user.username  # Use 'username' as the customer's name

    @property
    def meal_name(self):
        """Returns the name of the meal ordered."""
        return self.meal.name  # Assuming 'name' exists in the Meal model

    @property
    def formatted_date(self):
        """Returns a formatted string for the order date."""
        return self.date.strftime('%Y-%m-%d %H:%M:%S')

    def __repr__(self):
        """Represents the Order object with more details."""
        return f"<Order(id={self.id}, customer={self.user.username}, meal={self.meal.name}, " \
               f"status={self.status}, total_price=${self.total_price}, date={self.formatted_date})>"


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='notifications')

    def mark_as_read(self):
        """Mark the notification as read."""
        self.is_read = True
        db.session.commit()

    def __repr__(self):
        return f'<Notification {self.id} - {self.message}>'

class TokenBlocklist(db.Model):
    __tablename__ = 'token_blocklist'

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<TokenBlocklist {self.jti}>'