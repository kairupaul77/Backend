from flask import jsonify, request, Blueprint, redirect, url_for
from models import db, User, TokenBlocklist
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook

auth_bp = Blueprint("auth_bp", __name__)

# Configure social login blueprints
google_bp = make_google_blueprint(
    client_id="your-google-client-id",
    client_secret="your-google-client-secret",
    redirect_to="auth_bp.google_login",
)
auth_bp.register_blueprint(google_bp, url_prefix="/google")

github_bp = make_github_blueprint(
    client_id="your-github-client-id",
    client_secret="your-github-client-secret",
    redirect_to="auth_bp.github_login",
)
auth_bp.register_blueprint(github_bp, url_prefix="/github")

facebook_bp = make_facebook_blueprint(
    client_id="your-facebook-client-id",
    client_secret="your-facebook-client-secret",
    redirect_to="auth_bp.facebook_login",
)
auth_bp.register_blueprint(facebook_bp, url_prefix="/facebook")


# Helper function to create or get a user from social login
def create_or_get_user(email, social_id=None, provider=None):
    user = User.query.filter_by(email=email).first()
    if not user:
        # Create a new user if they don't exist
        user = User(
            email=email,
            password_hash=generate_password_hash("social-login"),  # Dummy password
            google_id=social_id if provider == "google" else None,
            github_id=social_id if provider == "github" else None,
            facebook_id=social_id if provider == "facebook" else None,
        )
        db.session.add(user)
        db.session.commit()
    return user


# Google login
@auth_bp.route("/google/login")
def google_login():
    if not google.authorized:
        return redirect(url_for("google.login"))

    # Fetch user info from Google
    resp = google.get("/oauth2/v2/userinfo")
    if not resp.ok:
        return jsonify({"error": "Failed to fetch user info from Google"}), 400

    google_data = resp.json()
    email = google_data["email"]
    google_id = google_data["id"]

    # Create or get the user
    user = create_or_get_user(email, google_id, "google")

    # Generate JWT token
    access_token = user.generate_auth_token()
    return jsonify({"access_token": access_token}), 200


# GitHub login
@auth_bp.route("/github/login")
def github_login():
    if not github.authorized:
        return redirect(url_for("github.login"))

    # Fetch user info from GitHub
    resp = github.get("/user")
    if not resp.ok:
        return jsonify({"error": "Failed to fetch user info from GitHub"}), 400

    github_data = resp.json()
    email = github_data.get("email")
    github_id = github_data["id"]

    # Create or get the user
    user = create_or_get_user(email, github_id, "github")

    # Generate JWT token
    access_token = user.generate_auth_token()
    return jsonify({"access_token": access_token}), 200


# Facebook login
@auth_bp.route("/facebook/login")
def facebook_login():
    if not facebook.authorized:
        return redirect(url_for("facebook.login"))

    # Fetch user info from Facebook
    resp = facebook.get("/me?fields=email,id")
    if not resp.ok:
        return jsonify({"error": "Failed to fetch user info from Facebook"}), 400

    facebook_data = resp.json()
    email = facebook_data.get("email")
    facebook_id = facebook_data["id"]

    # Create or get the user
    user = create_or_get_user(email, facebook_id, "facebook")

    # Generate JWT token
    access_token = user.generate_auth_token()
    return jsonify({"access_token": access_token}), 200


# Login
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        access_token = user.generate_auth_token()
        return jsonify({"access_token": access_token}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401


# Current User
@auth_bp.route("/current_user", methods=["GET"])
@jwt_required()
def current_user():
    current_user_id = get_jwt_identity()

    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user_data = {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "profile_img": user.profile_img,
    }

    return jsonify(user_data), 200


# Logout
@auth_bp.route("/logout", methods=["DELETE"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    now = datetime.now(timezone.utc)

    # Add the token to the blocklist
    db.session.add(TokenBlocklist(jti=jti, created_at=now))
    db.session.commit()

    return jsonify({"success": "Logged out successfully"}), 200