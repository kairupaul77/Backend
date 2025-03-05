from flask import jsonify, request, Blueprint, redirect, url_for
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from jwt.exceptions import ExpiredSignatureError

# Blueprint for auth routes
auth_bp = Blueprint("auth_bp", __name__)

# Login (Email and password-based)
@auth_bp.route("/login", methods=["POST"])
def login():
    from models import db, User  # Import here to avoid circular imports
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):  # Assuming check_password exists in User model
        access_token = create_access_token(identity=user.email)  # Use email as identity
        refresh_token = create_refresh_token(identity=user.email)  # Generate refresh token
        return jsonify(access_token=access_token, refresh_token=refresh_token), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401


# Get current user information with token expiration handling
@auth_bp.route("/current_user", methods=["GET"])
@jwt_required()
def current_user():
    from models import User  # Import here to avoid circular imports
    try:
        email = get_jwt_identity()  # Get the email from the JWT
        user = User.query.filter_by(email=email).first()

        if user:
            return jsonify({
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role
            }), 200
        else:
            return jsonify({"message": "User not found"}), 404
    except ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except Exception as e:
        print("Error in /current_user:", str(e))  # Log the error
        return jsonify({"error": "Unauthorized"}), 401


# Token Refresh Endpoint
@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    try:
        identity = get_jwt_identity()
        new_access_token = create_access_token(identity=identity)
        return jsonify(access_token=new_access_token), 200
    except Exception as e:
        return jsonify({"error": "Could not refresh token"}), 401


# Logout
@auth_bp.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    from models import db, TokenBlocklist  # Ensure db is imported

    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)

    # Add the token to the blocklist
    db.session.add(TokenBlocklist(jti=jti, created_at=now))
    db.session.commit()

    return jsonify({"success": "Logged out successfully"}), 200
@auth_bp.route("/login_with_google", methods=["POST"])
def login_with_google():
    from models import User  

    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()

    if user:
        access_token = create_access_token(identity=user.email)  # Use email as identity
        refresh_token = create_refresh_token(identity=user.email)  # Generate refresh token
        return jsonify(access_token=access_token, refresh_token=refresh_token), 200


    return jsonify({"error": "Email is incorrect"}), 401

