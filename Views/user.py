from flask import jsonify, request, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
from app import db, app, mail
from flask_mail import Message
from models import User, Meal, Menu, Order, Notification, Cart, CartItem, TokenBlocklist

user_bp = Blueprint("user_bp", __name__)

# Fetch all users
@user_bp.route("/users", methods=["GET"])
@jwt_required()
def fetch_users():
    users = User.query.all()

    user_list = []
    for user in users:
        user_list.append({
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'role': user.role,
            'profile_img': user.profile_img,
        })

    return jsonify(user_list)


# Add user (Registration)
@user_bp.route("/users", methods=["POST"])
def add_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Missing required fields (username, email, password)"}), 400

    check_username = User.query.filter_by(username=username).first()
    check_email = User.query.filter_by(email=email).first()

    if check_username or check_email:
        return jsonify({"error": "Username or email already exists"}), 409

    # Create a new user
    new_user = User(username=username, email=email)
    new_user.set_password(password)  # Hash and store the password

    db.session.add(new_user)
    db.session.commit()

    # Optional: Send welcome email
    try:
        msg = Message(
            subject="Welcome to Book-A-Meal",
            sender=app.config["MAIL_DEFAULT_SENDER"],
            recipients=[email],
            body="Thank you for registering with Book-A-Meal! We hope you enjoy our service."
        )
        mail.send(msg)
        return jsonify({"msg": "User registered successfully!"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500


# Update user details
@user_bp.route("/users/<int:user_id>", methods=["PATCH"])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()  # Get user from JWT token
    user = User.query.get(user_id)

    if not user or user.id != current_user_id:
        return jsonify({"error": "User doesn't exist or unauthorized"}), 404

    data = request.get_json()
    username = data.get('username', user.username)
    email = data.get('email', user.email)
    password = data.get('password')

    # Check if the new username or email already exists
    if username != user.username:
        check_username = User.query.filter_by(username=username).first()
        if check_username:
            return jsonify({"error": "Username already exists"}), 409

    if email != user.email:
        check_email = User.query.filter_by(email=email).first()
        if check_email:
            return jsonify({"error": "Email already exists"}), 409

    # Update user details
    user.username = username
    user.email = email
    if password:
        user.set_password(password)  # Hash and store the new password

    db.session.commit()
    return jsonify({"success": "User updated successfully"}), 200


# Delete user
@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()  # Get user from JWT token
    user = User.query.get(user_id)

    if not user or user.id != current_user_id:
        return jsonify({"error": "User doesn't exist or unauthorized to delete this user"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"success": "User deleted successfully"}), 200


# User Login - Generate JWT Token
@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401


# Password Reset Request (send email)
@user_bp.route("/password-reset", methods=["POST"])
def password_reset():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Email not found"}), 404

    # Generate a reset token (this is a simple example; use a proper token generation mechanism in production)
    reset_token = generate_password_hash(user.email + str(datetime.utcnow()))  # Example token

    try:
        msg = Message(
            subject="Password Reset Request",
            sender=app.config["MAIL_DEFAULT_SENDER"],
            recipients=[email],
            body=f"To reset your password, click the link: /reset-password/{reset_token}"
        )
        mail.send(msg)
        return jsonify({"msg": "Password reset link sent to email"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500


# Password Reset - Update Password
@user_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password(token):
    data = request.get_json()
    new_password = data.get('password')

    if not new_password:
        return jsonify({"error": "New password is required"}), 400

    # Decrypt and validate token (this is a simple example; use a proper token validation mechanism in production)
    user = User.query.filter_by(email=token).first()  # Example based on email being used as token (change for real use)
    if not user:
        return jsonify({"error": "Invalid or expired reset token"}), 400

    # Update the user's password
    user.set_password(new_password)
    db.session.commit()

    return jsonify({"msg": "Password updated successfully"}), 200