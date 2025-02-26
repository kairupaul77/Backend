from flask import jsonify, request, Blueprint

from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

admin_bp = Blueprint("admin_bp", __name__)

# Admin: Add a New Meal Option
@admin_bp.route("/admin/meals", methods=["POST"])
@jwt_required()
def add_meal():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'caterer':
        return jsonify({"error": "Access denied, caterer privileges required"}), 403

    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    image_url = data.get('image_url')

    if not name or not price or not image_url:
        return jsonify({"error": "Meal name, price, and image URL are required"}), 400

    if Meal.query.filter_by(name=name).first():
        return jsonify({"error": "Meal already exists"}), 400

    new_meal = Meal(name=name, price=price, image_url=image_url)
    db.session.add(new_meal)
    db.session.commit()
    return jsonify({"msg": f"Meal '{name}' added successfully!"}), 201

# Admin: Modify a Meal Option
@admin_bp.route("/admin/meals/<int:meal_id>", methods=["PUT"])
@jwt_required()
def modify_meal(meal_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'caterer':
        return jsonify({"error": "Access denied, caterer privileges required"}), 403

    meal = Meal.query.get(meal_id)
    if not meal:
        return jsonify({"error": "Meal not found"}), 404

    data = request.get_json()
    meal.name = data.get('name', meal.name)
    meal.price = data.get('price', meal.price)
    meal.image_url = data.get('image_url', meal.image_url)
    db.session.commit()
    return jsonify({"msg": f"Meal '{meal.name}' updated successfully!"}), 200

# Admin: Delete a Meal Option
@admin_bp.route("/admin/meals/<int:meal_id>", methods=["DELETE"])
@jwt_required()
def delete_meal(meal_id):
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

# Admin: Set Up a Menu for a Specific Day
@admin_bp.route("/admin/menu", methods=["POST"])
@jwt_required()
def setup_menu():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'caterer':
        return jsonify({"error": "Access denied, caterer privileges required"}), 403

    data = request.get_json()
    date = datetime.strptime(data.get('date'), "%Y-%m-%d").date()
    meal_ids = data.get('meal_ids', [])
    
    if not meal_ids:
        return jsonify({"error": "At least one meal must be selected"}), 400

    Menu.query.filter_by(date=date).delete()  # Remove existing menu for the day
    
    for meal_id in meal_ids:
        meal = Meal.query.get(meal_id)
        if meal:
            new_menu_item = Menu(date=date, meal_id=meal_id)
            db.session.add(new_menu_item)
    
    db.session.commit()
    return jsonify({"msg": "Menu updated successfully!"}), 201

# Admin: View All Orders
@admin_bp.route("/admin/orders", methods=["GET"])
@jwt_required()
def fetch_all_orders():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'caterer':
        return jsonify({"error": "Access denied, caterer privileges required"}), 403

    orders = Order.query.all()
    order_list = []
    for order in orders:
        meal = Meal.query.get(order.meal_id)
        order_list.append({
            'order_id': order.id,
            'user_id': order.user_id,
            'meal': meal.name,
            'order_date': order.order_date.strftime("%Y-%m-%d %H:%M:%S"),
            'price': meal.price,
            'image_url': meal.image_url
        })
    return jsonify(order_list), 200

# Admin: View Earnings for the Day
@admin_bp.route("/admin/earnings", methods=["GET"])
@jwt_required()
def view_earnings():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'caterer':
        return jsonify({"error": "Access denied, caterer privileges required"}), 403

    today = datetime.utcnow().date()
    orders_today = Order.query.filter(Order.order_date >= today).all()
    total_earnings = sum(Meal.query.get(order.meal_id).price for order in orders_today)

    return jsonify({"total_earnings": total_earnings}), 200
