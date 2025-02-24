from flask import jsonify, request, Blueprint
from models import db, Meal, Order, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

admin_bp = Blueprint("admin_bp", __name__)

# Admin: Add a New Meal Option
@admin_bp.route("/admin/meals", methods=["POST"])
@jwt_required()
def add_meal():
    # Caterer check
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'caterer':
        return jsonify({"error": "Access denied, caterer privileges required"}), 403

    data = request.get_json()
    name = data.get('name')
    price = data.get('price')

    if not name or not price:
        return jsonify({"error": "Meal name and price are required"}), 400

    new_meal = Meal(name=name, price=price)
    db.session.add(new_meal)
    db.session.commit()

    return jsonify({"msg": f"Meal '{name}' added successfully!"}), 201

# Admin: View All Orders
@admin_bp.route("/admin/orders", methods=["GET"])
@jwt_required()
def fetch_all_orders():
    # Caterer check
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'caterer':
        return jsonify({"error": "Access denied, caterer privileges required"}), 403

    orders = Order.query.all()
    if not orders:
        return jsonify({"msg": "No orders found"}), 404

    order_list = []
    for order in orders:
        meal = Meal.query.get(order.meal_id)  # Get meal information from the Meal table
        order_list.append({
            'order_id': order.id,
            'user_id': order.user_id,
            'meal': meal.name,
            'order_date': order.order_date.strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify(order_list), 200

# Admin: View Earnings for the Day
@admin_bp.route("/admin/earnings", methods=["GET"])
@jwt_required()
def view_earnings():
    # Caterer check
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'caterer':
        return jsonify({"error": "Access denied, caterer privileges required"}), 403

    # Calculate total earnings for the day
    today = datetime.utcnow().date()
    orders_today = Order.query.filter(Order.order_date >= today).all()

    if not orders_today:
        return jsonify({"msg": "No orders for today"}), 200

    total_earnings = 0
    for order in orders_today:
        meal = Meal.query.get(order.meal_id)
        total_earnings += meal.price  # Assuming each meal has a 'price' attribute

    return jsonify({"total_earnings": total_earnings}), 200

# Admin: Delete a Meal Option
@admin_bp.route("/admin/meals/<int:meal_id>", methods=["DELETE"])
@jwt_required()
def delete_meal(meal_id):
    # Caterer check
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'caterer':
        return jsonify({"error": "Access denied, caterer privileges required"}), 403

    meal = Meal.query.get(meal_id)
    if not meal:
        return jsonify({"error": "Meal not found"}), 404

    db.session.delete(meal)
    db.session.commit()
    
    return jsonify({"msg": f"Meal '{meal.name}' deleted successfully!"}), 200
