from flask import jsonify, request, Blueprint, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
from extensions import db, mail  # Assuming `db` and `mail` are initialized in extensions.py
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from models import User, Meal, TokenBlocklist

user_bp = Blueprint("user_bp", __name__)




# Add user (Registration)
@user_bp.route("/users", methods=["POST"])
def add_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Missing required fields (username, email, password)"}), 400

    # Check for existing username or email
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({"error": "Username or email already exists"}), 409

    new_user = User(username=username, email=email)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    # Send welcome email
    try:
        msg = Message(
            subject="Welcome to Book-A-Meal",
            sender=current_app.config["MAIL_DEFAULT_SENDER"],
            recipients=[email],
            body="Thank you for registering with Book-A-Meal! We hope you enjoy our service."
        )
        mail.send(msg)
        return jsonify({"msg": "User registered successfully!"}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

# Update user details (username, email, password, and role)
@user_bp.route("/users/<int:user_id>", methods=["PATCH"])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(user_id)  # User to be updated

    if not user:
        return jsonify({"error": "User doesn't exist"}), 404

    data = request.get_json()
    username = data.get('username', user.username)
    email = data.get('email', user.email)
    password = data.get('password')
    new_role = data.get('role')

    # Validate role (optional, if role changes are needed)
    if new_role and new_role not in ["customer", "admin", "caterer"]:
        return jsonify({"error": "Invalid role"}), 400

    user.role = new_role if new_role else user.role  # Allow role update without restriction

    # Check if the new username or email already exists
    if username != user.username and User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409

    if email != user.email and User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 409

    # Apply updates
    user.username = username
    user.email = email
    if password:
        user.set_password(password)

    db.session.commit()
    return jsonify({
        "success": "User updated successfully",
        "new_role": user.role
    }), 200


# Delete user
@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()
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

    # Generate reset token
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    reset_token = s.dumps(email, salt='password-reset')

    try:
        msg = Message(
            subject="Password Reset Request",
            sender=current_app.config["MAIL_DEFAULT_SENDER"],
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

    # Verify and decrypt the token
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = s.loads(token, salt='password-reset', max_age=3600)  # Token expires in 1 hour
    except Exception:
        return jsonify({"error": "Invalid or expired reset token"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Update the user's password
    user.set_password(new_password)
    db.session.commit()

    return jsonify({"msg": "Password updated successfully"}), 200
