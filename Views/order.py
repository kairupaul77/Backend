import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db, Order, User, Meal, Notification, Menu

# Store the last fetched orders timestamp globally (in-memory storage for simplicity)
last_fetched_time = None

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Define the Blueprint
order_bp = Blueprint('order_bp', __name__)

# Helper function to check if a user is an admin
def is_admin(user):
    return user and user.role == "admin"

@order_bp.route('/orders/add', methods=['POST'])
@jwt_required()
def add_order_route():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    if not user:
        logging.debug(f"User not found for email: {email}")
        return jsonify({'message': 'User not found'}), 404

    try:
        data = request.get_json()
        logging.debug(f"Received payload in /orders/add: {data}")

        items = data.get('items')
        if not isinstance(items, list) or not items:
            logging.debug(f"Invalid items format received: {items}")
            return jsonify({'message': 'Invalid items format, expected an array'}), 400

        order_date = datetime.today().date()
        total_price = 0.0
        orders = []

        for item in items:
            menu_id = item.get('menu_id') or item.get('id')
            quantity = item.get('quantity', 1)
            price = item.get('price', 0.0)

            menu = Menu.query.get(menu_id)
            if not menu:
                logging.debug(f"Menu not found for id: {menu_id}")
                return jsonify({'message': f'Menu with id {menu_id} not found'}), 404

            total_price += price * quantity

            new_order = Order(
                user_id=user.id,
                menu_id=menu.id,
                date=order_date,
                quantity=quantity,
                total_price=price * quantity,
                payment_status=False  # Default to "Not Paid"
            )
            orders.append(new_order)

        db.session.add_all(orders)
        db.session.commit()
        logging.debug(f"Order created successfully for user {user.id}")

        return jsonify({
            'message': 'Order placed successfully',
            'total_price': total_price,
            'payment_status': "Paid" if new_order.payment_status else "Not Paid"
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating order: {str(e)}")
        return jsonify({'message': 'Internal server error'}), 500



# Get All Orders (Admin Only)
# Get All Orders (Admin Only)
@order_bp.route('/orders/admin-history', methods=['GET'])
@jwt_required()
def get_orders():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    if not is_admin(user):
        logging.debug(f"Unauthorized access attempt by user: {email}")
        return jsonify({'message': 'Unauthorized. Admins only.'}), 403

    # Fetch all orders without filtering by date
    orders = Order.query.all()

    return jsonify({'orders': [
        {
            'id': order.id,
            'user_id': order.user_id,
            'menu_id': order.menu_id,
            'meal_id': order.meal_id,
            'date': order.date.strftime('%Y-%m-%d'),
            'quantity': order.quantity,
            'total_price': order.total_price,
            'status': order.status,  # Order status (e.g., pending, completed)
        }
        for order in orders
    ]})

@order_bp.route('/orders/revenue', methods=['GET'])
@jwt_required()
def get_revenue():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    if not is_admin(user):
        logging.debug(f"Unauthorized access attempt by user: {email}")
        return jsonify({'message': 'Unauthorized. Admins only.'}), 403

    # Get date from query parameters, default to today
    date_str = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # Log the date to ensure correct date is being passed
    logging.debug(f"Fetching revenue for date: {date_obj}")

    # Check if there are orders for the given date
    orders_today = Order.query.filter(db.func.date(Order.date) == date_obj).all()
    for order in orders_today:
        logging.debug(f"Order ID: {order.id}, Date: {order.date}, Total Price: {order.total_price}")

    # Calculate total revenue and order count for the given date
    revenue = db.session.query(db.func.sum(Order.total_price)) \
        .filter(db.func.date(Order.date) == date_obj) \
        .scalar()

    order_count = db.session.query(db.func.count(Order.id)) \
        .filter(db.func.date(Order.date) == date_obj) \
        .scalar()

    logging.debug(f"Total revenue for {date_obj}: {revenue}, Total orders: {order_count}")
    
    return jsonify({
        'revenue': revenue if revenue is not None else 0,
        'total_orders': order_count if order_count is not None else 0
    })


# Order History for Customers
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
            'total_price': order.total_price,
            'payment_status': 'Paid' if user.role == 'customer' else order.payment_status  # Only show 'Paid' to customers
        }
        for order in orders
    ]})



# Admin Order History (Admin Only)@order_bp.route('/order-history', methods=['GET'])
@jwt_required()  # Ensures the user is logged in
def get_admin_order_history():
    email = get_jwt_identity()  # Get the email of the current user
    
    # Fetch the user from the database based on the email
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    # Check if the user is an admin
    if user.role != 'admin':
        return jsonify({"message": "Access denied. Admins only."}), 403
    
    # Query all orders from the database
    orders = Order.query.all()
    
    # Serialize orders to return to the frontend
    order_list = [{
        'id': order.id,
        'customer_name': order.user.username,  # Using 'username' as the customer name
        'menu_date': order.menu.date.strftime('%Y-%m-%d') if order.menu else "No menu assigned",  # Use 'menu_date'
        'meal': order.meal.name if order.meal else "No meal assigned",  # Use 'meal' name (not ID)
        'quantity': order.quantity,
        'status': order.status,
        'order_date': order.date.strftime('%Y-%m-%d %H:%M:%S')  # Format the order date
    } for order in orders]
    
    return jsonify({"orders": order_list}), 200



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