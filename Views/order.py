import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db, Order, User, Meal, Notification, Menu

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define the Blueprint
order_bp = Blueprint('order_bp', __name__)

# Helper function to check if a user is an admin
def is_admin(user):
    return user and user.role == "admin"

# Customer Creates an Order
@order_bp.route('/orders/add', methods=['POST'])
@jwt_required()
def add_order_route():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    if not user:
        logging.debug(f"User not found for email: {email}")
        return jsonify({'message': 'User not found'}), 404

    data = request.get_json()
    logging.debug(f"Received payload: {data}")

    # Validate menu_id
    menu = Menu.query.get(data.get('menu_id'))
    if not menu:
        logging.debug(f"Menu not found for id: {data.get('menu_id')}")
        return jsonify({'message': 'Menu not found'}), 404

    # Validate meal_id (if required)
    meal_id = data.get('meal_id')
    if meal_id is None:
        logging.debug("meal_id is required but not provided")
        return jsonify({'message': 'meal_id is required'}), 400

    # Validate date
    try:
        order_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    except (ValueError, KeyError):
        logging.debug("Invalid or missing date format")
        return jsonify({'message': 'Invalid or missing date format, expected YYYY-MM-DD'}), 400

    # Check if the user already has an order for this date
    if Order.query.filter_by(user_id=user.id, date=order_date).first():
        logging.debug(f"User {user.id} already has an order for date: {order_date}")
        return jsonify({'message': 'You have already placed an order for this date'}), 400

    # Create new order
    try:
        new_order = Order(
            user_id=user.id,
            menu_id=menu.id,
            meal_id=meal_id,
            date=order_date,
            quantity=data.get('quantity', 1),
            total_price=data.get('total_price', 0.0)
        )
        db.session.add(new_order)
        db.session.commit()
        logging.debug(f"Order created successfully for user {user.id}")
        return jsonify({'message': 'Order placed successfully'}), 201
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating order: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

# Order Management (Admin)
@order_bp.route('/orders/change', methods=['POST'])
@jwt_required()
def change_order():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    if not is_admin(user):
        logging.debug(f"Unauthorized access attempt by user: {email}")
        return jsonify({'message': 'Unauthorized. Admins only.'}), 403

    data = request.get_json()
    logging.debug(f"Received payload: {data}")

    order = Order.query.get(data.get('order_id'))
    if not order:
        logging.debug(f"Order not found for id: {data.get('order_id')}")
        return jsonify({'message': 'Order not found'}), 404

    new_menu = Menu.query.get(data.get('new_menu_id'))
    if not new_menu:
        logging.debug(f"New menu not found for id: {data.get('new_menu_id')}")
        return jsonify({'message': 'New menu item not found'}), 404

    try:
        order.menu_id = new_menu.id
        db.session.commit()
        logging.debug(f"Order {order.id} updated successfully")
        return jsonify({'message': 'Order updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating order: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500

# Get All Orders (Admin Only)
@order_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    if not is_admin(user):
        logging.debug(f"Unauthorized access attempt by user: {email}")
        return jsonify({'message': 'Unauthorized. Admins only.'}), 403

    orders = Order.query.all()
    return jsonify({'orders': [
        {
            'id': order.id,
            'user_id': order.user_id,
            'menu_id': order.menu_id,
            'meal_id': order.meal_id,
            'date': order.date.strftime('%Y-%m-%d'),
            'quantity': order.quantity,
            'total_price': order.total_price
        }
        for order in orders
    ]})

# Get Revenue (Admin Only)
@order_bp.route('/orders/revenue', methods=['GET'])
@jwt_required()
def get_revenue():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    if not is_admin(user):
        logging.debug(f"Unauthorized access attempt by user: {email}")
        return jsonify({'message': 'Unauthorized. Admins only.'}), 403

    revenue = db.session.query(db.func.sum(Order.total_price)).scalar()
    logging.debug(f"Total revenue: {revenue}")
    return jsonify({'revenue': revenue or 0})

# Order History for Customers
@order_bp.route('/orders/history', methods=['GET'])
@jwt_required()
def get_order_history():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    if not user:
        logging.debug(f"User not found for email: {email}")
        return jsonify({'message': 'User not found'}), 404

    orders = Order.query.filter_by(user_id=user.id).all()
    return jsonify({'orders': [
        {
            'id': order.id,
            'menu_id': order.menu_id,
            'meal_id': order.meal_id,
            'date': order.date.strftime('%Y-%m-%d'),
            'quantity': order.quantity,
            'total_price': order.total_price
        }
        for order in orders
    ]})

# Admin Order History (Admin Only)
@order_bp.route('/orders/admin-history', methods=['GET'])
@jwt_required()
def get_admin_order_history():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    if not is_admin(user):
        logging.debug(f"Unauthorized access attempt by user: {email}")
        return jsonify({'message': 'Unauthorized. Admins only.'}), 403

    orders = Order.query.all()
    return jsonify({'orders': [
        {
            'id': order.id,
            'user_id': order.user_id,
            'menu_id': order.menu_id,
            'meal_id': order.meal_id,
            'date': order.date.strftime('%Y-%m-%d'),
            'quantity': order.quantity,
            'total_price': order.total_price
        }
        for order in orders
    ]})

# Notifications for Users
# notifications_bp = Blueprint('notifications_bp', __name__)

# def send_notification_to_all(message):
#     """Send a notification to all users when the daily menu is set."""
#     users = User.query.filter_by(role='customer').all()
#     notifications = [Notification(user_id=user.id, message=message) for user in users]
#     db.session.bulk_save_objects(notifications)
#     db.session.commit()

# @notifications_bp.route('/set_daily_menu', methods=['POST'])
# @jwt_required()
# def set_daily_menu():
#     """Set daily menu and notify customers."""
#     message = "Today's menu has been set! Check it out now."
#     send_notification_to_all(message)
#     return jsonify({"message": "Daily menu set, notifications sent."}), 201