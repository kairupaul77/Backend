from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128))
    role = db.Column(db.String(20), default='customer')  # 'customer' or 'caterer'
    profile_img = db.Column(db.String(256))
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)
    google_id = db.Column(db.String(100))

    # Relationships
    meals = db.relationship('Meal', backref='caterer', lazy=True)
    menus = db.relationship('Menu', backref='caterer', lazy=True)
    orders = db.relationship('Order', backref='customer', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    carts = db.relationship('Cart', backref='user', lazy=True)

  
class Meal(db.Model):
    __tablename__ = 'meals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    caterer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationships
    carts = db.relationship('CartItem', backref='meal', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price
        }


class Menu(db.Model):
    __tablename__ = 'menus'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    caterer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meals = db.relationship('Meal', secondary='menu_meals', lazy='subquery')

menu_meals = db.Table('menu_meals',
    db.Column('menu_id', db.Integer, db.ForeignKey('menus.id'), primary_key=True),
    db.Column('meal_id', db.Integer, db.ForeignKey('meals.id'), primary_key=True)
)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menus.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    total_price = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        meal = Meal.query.get(self.meal_id)
        menu = Menu.query.get(self.menu_id)
        return {
            'id': self.id,
            'user_id': self.user_id,
            'menu_id': self.menu_id,
            'meal_id': self.meal_id,
            'meal_name': meal.name,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'menu_date': menu.date.strftime('%Y-%m-%d'),
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }



class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')  # Formatting date
        }

class Cart(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with CartItem
    items = db.relationship('CartItem', back_populates='cart', cascade="all, delete-orphan")

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    # Relationships
    cart = db.relationship('Cart', back_populates='items')
    meal = db.relationship('Meal', backref=db.backref('cart_items', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'cart_id': self.cart_id,
            'meal_id': self.meal_id,
            'quantity': self.quantity,
            'meal': {
                'name': self.meal.name,
                'price': self.meal.price
            }
        }
        
class TokenBlocklist(db.Model):
    _tablename_ = 'token_blocklist'
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False)  # JWT ID (unique identifier for the token)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Timestamp of when the token was revoked

    def _repr_(self):
        return f"<TokenBlocklist {self.jti}>"        