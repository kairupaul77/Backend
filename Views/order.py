from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from datetime import datetime

order_bp = Blueprint('order_bp', __name__)

@order_bp.route('/order', methods=['POST'])
@jwt_required()
def create_order():
    current_user = User.query.get(get_jwt_identity())
    data = request.json

    # Ensure 'menu_id', 'meal_id', and 'quantity' are provided
    if not all(key in data for key in ('menu_id', 'meal_id', 'quantity')):
        return jsonify({"error": "Missing required fields (menu_id, meal_id, quantity)"}), 400

    try:
        menu = Menu.query.get(data['menu_id'])
        meal = Meal.query.get(data['meal_id'])
        
        # Check if menu or meal exists
        if not menu or not meal:
            return jsonify({"error": "Menu or Meal not found"}), 404

        # Ensure the meal is part of the menu
        if meal not in menu.meals:
            return jsonify({"error": "Meal is not available in the selected menu"}), 400

        # Calculate total price
        total_price = meal.price * data['quantity']

        # Create the order
        order = Order(
            user_id=current_user.id,
            menu_id=menu.id,
            meal_id=meal.id,
            quantity=data['quantity'],
            total_price=total_price
        )

        # Save to database
        db.session.add(order)
        db.session.commit()

        # Return the created order as a response
        return jsonify(order.to_dict()), 201

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500