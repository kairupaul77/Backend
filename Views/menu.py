from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, datetime
from models import db, Menu, Meal, User

menu_bp = Blueprint('menu', __name__)

def validate_date(date_str):
    """Helper function to validate date format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

# Admin: Set up a menu for a specific day
@menu_bp.route('/menu', methods=['POST'])
@jwt_required()
def create_menu():
    """
    Admin sets up a menu by selecting meals for a specific date.
    """
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).one_or_none()

    if not user or user.role != 'admin':
        return jsonify({'error': 'Access denied. Only admins can create menus'}), 403

    data = request.get_json()
    menu_date = validate_date(data.get('date', str(date.today())))

    if not menu_date:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    if Menu.query.filter_by(date=menu_date).first():
        return jsonify({'error': 'A menu already exists for this date'}), 400

    meal_ids = data.get('meals', [])
    if not meal_ids:
        return jsonify({'error': 'Please select at least one meal for the menu'}), 400

    meals = Meal.query.filter(Meal.id.in_(meal_ids)).all()
    missing_meals = set(meal_ids) - {meal.id for meal in meals}

    if missing_meals:
        return jsonify({'error': f'Meal(s) with ID(s) {list(missing_meals)} not found'}), 404

    new_menu = Menu(date=menu_date)
    new_menu.meals.extend(meals)
    db.session.add(new_menu)
    db.session.commit()

    return jsonify({'message': 'Menu created successfully'}), 201

# Get menu for a specific day
@menu_bp.route('/menu/<string:menu_date>', methods=['GET'])
@jwt_required()
def get_menu(menu_date):
    menu_date_obj = validate_date(menu_date)
    if not menu_date_obj:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    menu = Menu.query.filter_by(date=menu_date_obj).first()
    if not menu:
        return jsonify({'error': 'No menu found for this date'}), 404

    # Convert menu.date to a datetime.date object if it's a string
    if isinstance(menu.date, str):
        menu_date_obj = datetime.strptime(menu.date, '%Y-%m-%d').date()
    else:
        menu_date_obj = menu.date

    return jsonify({
        'date': menu_date_obj.strftime('%Y-%m-%d'),
        'meals': [{'id': meal.id, 'name': meal.name, 'price': meal.price, 'image':meal.image_url} for meal in menu.meals],
        'menu_id':menu.id
    }), 200

# Customers select a meal from the menu
@menu_bp.route('/menu/select', methods=['POST'])
@jwt_required()
def select_meal():
    """
    Customers can select a meal from the available menu.
    """
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).one_or_none()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    menu_date = validate_date(data.get('date', str(date.today())))
    if not menu_date:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    menu = Menu.query.filter_by(date=menu_date).first()
    if not menu:
        return jsonify({'error': 'No menu available for this date'}), 404

    try:
        meal_id = int(data.get('meal_id'))
    except (ValueError, TypeError):
        return jsonify({'error': 'Meal ID must be an integer'}), 400

    meal = Meal.query.get(meal_id)
    if not meal or meal not in menu.meals:
        return jsonify({'error': 'Selected meal is not on the menu for this date'}), 404

    return jsonify({'message': f'You have selected {meal.name} from the menu'}), 200
