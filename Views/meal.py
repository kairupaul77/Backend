from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Meal, User, db

meal_bp = Blueprint("meal", __name__, url_prefix="/meal")

@meal_bp.route("/add", methods=["POST"])
@jwt_required()
def add_meal():
    email = get_jwt_identity()
    print(f"JWT Identity (Email): {email}")  # Debugging log

    user = User.query.filter_by(email=email).first()
    if not user:
        print("User not found in database")  # Debugging log
        return jsonify({"message": "User not found"}), 404

    if not user.is_admin:
        print("User is not an admin")  # Debugging log
        return jsonify({"message": "Unauthorized - Not an Admin"}), 403

    data = request.get_json()
    new_meal = Meal(
        name=data["name"],
        price=data["price"],
        image_url=data["image_url"],
        caterer_id=user.id  # Assign the logged-in admin's ID
    )

    db.session.add(new_meal)
    db.session.commit()

    return jsonify({"message": "Meal added successfully!"}), 201

@meal_bp.route("/update/<int:meal_id>", methods=["PUT"])
@jwt_required()
def update_meal(meal_id):
    print("request headers are ",request.headers)
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user or not user.is_admin:
        return jsonify({"message": "Unauthorized"}), 403

    data = request.get_json()
    meal = Meal.query.get_or_404(meal_id)

    meal.name = data.get("name", meal.name)
    meal.price = data.get("price", meal.price)
    meal.image_url = data.get("image_url", meal.image_url)

    db.session.commit()
    return jsonify({"message": "Meal updated successfully!"}), 200

@meal_bp.route("/delete/<int:meal_id>", methods=["DELETE"])
@jwt_required()
def delete_meal(meal_id):
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    if not user or not user.is_admin:
        return jsonify({"message": "Unauthorized"}), 403

    meal = Meal.query.get(meal_id)
    if meal is None:
        return jsonify({"error": "Meal not found"}), 404

    db.session.delete(meal)
    db.session.commit()
    return jsonify({"message": "Meal deleted successfully!"}), 200

@meal_bp.route("/all", methods=["GET"])
def get_meals():
    meals = Meal.query.all()
    if not meals:
        return jsonify({"message": "No meals available"}), 404

    meal_list = [
        {"id": m.id, "name": m.name, "price": m.price, "image_url": m.image_url} for m in meals
    ]
    return jsonify({"meals": meal_list}), 200
