from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity


cart_bp = Blueprint('cart_bp', __name__, )

@cart_bp.route('/items', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()

    # Check if the cart exists for the user, otherwise create one
    cart = Cart.query.filter_by(user_id=user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.session.add(cart)
        db.session.commit()  # Commit after creating a new cart

    # Get request data
    data = request.json
    
    # Ensure 'meal_id' is present in the request data
    if 'meal_id' not in data:
        return jsonify({'message': 'Missing meal_id in request data'}), 400

    # Check if the meal exists in the database
    meal = Meal.query.get(data['meal_id'])
    if not meal:
        return jsonify({'message': 'Meal not found'}), 404

    # Check if the cart already contains this item and update or add new item
    item = CartItem.query.filter_by(cart_id=cart.id, meal_id=data['meal_id']).first()
    
    if item:
        item.quantity += data.get('quantity', 1)  # Update quantity if item already exists
    else:
        item = CartItem(
            cart_id=cart.id,
            meal_id=data['meal_id'],
            quantity=data.get('quantity', 1)
        )
        db.session.add(item)

    # Commit changes to the database
    db.session.commit()

    return jsonify(item.to_dict()), 201