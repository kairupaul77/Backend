from flask import jsonify, request, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db, app, mail
from flask_mail import Message
from models import User, Cart, Meal, Order

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
            'is_approved': user.is_approved,
            'is_admin': user.is_admin,
            'username': user.username,
        })

    return jsonify(user_list)


# Add user (Registration)
@user_bp.route("/users", methods=["POST"])
def add_user():
    data = request.get_json()
    username = data['username']
    email = data['email']
    password = generate_password_hash(data['password'])

    check_username = User.query.filter_by(username=username).first()
    check_email = User.query.filter_by(email=email).first()

    if check_username or check_email:
        return jsonify({"error": "Username/email exists"}), 406
    else:
        new_user = User(username=username, email=email, password=password)
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
            return jsonify({"msg": "User saved successfully!"}), 201
        except Exception as e:
            return jsonify({"error": f"Failed to send email: {str(e)}"}), 406


# Update user details
@user_bp.route("/users/<int:user_id>", methods=["PATCH"])
@jwt_required()
def update_user(user_id):
    current_user_id = get_jwt_identity()  # Get user from JWT token
    user = User.query.get(user_id)

    if user and user.id == current_user_id:
        data = request.get_json()
        username = data.get('username', user.username)
        email = data.get('email', user.email)
        password = data.get('password', user.password)

        check_username = User.query.filter_by(username=username).first()
        check_email = User.query.filter_by(email=email).first()

        if (check_username and check_username.id != user.id) or (check_email and check_email.id != user.id):
            return jsonify({"error": "Username/email exists"}), 406

        user.username = username
        user.email = email
        user.password = generate_password_hash(password) if password else user.password

        db.session.commit()
        return jsonify({"success": "Updated successfully"}), 200
    else:
        return jsonify({"error": "User doesn't exist or unauthorized"}), 404


# Delete user
@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    current_user_id = get_jwt_identity()  # Get user from JWT token
    user = User.query.get(user_id)

    if user and user.id == current_user_id:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"success": "Deleted successfully"}), 200
    else:
        return jsonify({"error": "User doesn't exist or unauthorized to delete this user"}), 404


# User Login - Generate JWT Token
@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data['email']
    password = data['password']

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401


# Password Reset Request (send email)
@user_bp.route("/password-reset", methods=["POST"])
def password_reset():
    data = request.get_json()
    email = data['email']

    user = User.query.filter_by(email=email).first()
    if user:
        reset_token = generate_password_hash(user.email)  # Token can be an encrypted unique string
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
    else:
        return jsonify({"error": "Email not found"}), 404


# Password Reset - Update Password
@user_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password(token):
    data = request.get_json()
    new_password = data['password']

    # Decrypt and validate token (implementation based on your security mechanism)
    user = User.query.filter_by(email=token).first()  # Example based on email being used as token (change for real use)
    if user:
        user.password = generate_password_hash(new_password)
        db.session.commit()
        return jsonify({"msg": "Password updated successfully"}), 200
    else:
        return jsonify({"error": "Invalid or expired reset token"}), 400
