from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Menu, Meal, User, db
from datetime import datetime

menu_bp = Blueprint('menu_bp', __name__)

@menu_bp.route('/menu', methods=['POST'])
@jwt_required()
def create_menu():
    # Ensure the user is a caterer
    current_user = User.query.get(get_jwt_identity())
    if current_user.role != 'caterer':
        return jsonify({"error": "Unauthorized"}), 403

    # Parse incoming data
    data = request.json
    try:
        # Create a new menu
        menu = Menu(
            date=datetime.strptime(data['date'], '%Y-%m-%d'),
            caterer_id=current_user.id
        )

        # Add meals to the menu using provided meal IDs
        for meal_id in data['meal_ids']:
            meal = Meal.query.get(meal_id)
            if meal:
                menu.meals.append(meal)

        # Add the menu to the session and commit
        db.session.add(menu)
        db.session.commit()

        # Return a JSON response with the menu details
        return jsonify(menu.to_dict()), 201
    except KeyError as e:
        return jsonify({"error": f"Missing key: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500