from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Meal, User, db
from utils.pagination import paginate

meal_bp = Blueprint('meal_bp', __name__)

# Create a meal (only for caterers)
@meal_bp.route('/meal', methods=['POST'])
@jwt_required()
def create_meal():
    current_user = User.query.get(get_jwt_identity())
    
    # Check if the user is a caterer
    if current_user.role != 'caterer':
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    # Validate if 'name' and 'price' are provided in the request
    if 'name' not in data or 'price' not in data:
        return jsonify({"error": "Missing 'name' or 'price' in request data"}), 400
    
    meal = Meal(
        name=data['name'],
        price=data['price'],
        caterer_id=current_user.id
    )
    db.session.add(meal)
    db.session.commit()
    return jsonify(meal.to_dict()), 201

# Get meals for the current caterer with pagination
@meal_bp.route('/meal', methods=['GET'])
@jwt_required()
def get_meals():
    current_user = User.query.get(get_jwt_identity())
    
    # Query meals belonging to the current caterer
    query = Meal.query.filter_by(caterer_id=current_user.id)
    
    # Apply pagination utility (make sure this function handles pagination properly)
    return paginate(query, Meal)