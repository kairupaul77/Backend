from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Notification
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__)

def send_notification_to_all(message):
    """Send a notification to all customers when the daily menu is set."""
    users = User.query.filter_by(role='customer').all()
    
    if not users:
        print("No customers found to send notifications.")
        return
    
    notifications = []
    for user in users:
        notification = Notification(user_id=user.id, message=message)
        notifications.append(notification)
        print(f"Sending notification to user {user.id}: {message}")  # Debugging

    db.session.bulk_save_objects(notifications)
    db.session.commit()
    
    print("Notifications committed to DB:", notifications)

@notifications_bp.route('/set_daily_menu', methods=['POST'])
@jwt_required()
def set_daily_menu():
    """Set daily menu and notify customers."""
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    # Check if the user is an admin
    if not user or user.role != "admin":
        return jsonify({"message": "Unauthorized. Admins only."}), 403

    # Send notifications to all customers
    message = "Today's menu has been set! Check it out now."
    send_notification_to_all(message)

    return jsonify({"message": "Daily menu set, notifications sent."}), 201

@notifications_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Retrieve all notifications for the logged-in user."""
    user_id = get_jwt_identity()
    print(f"DEBUG: JWT Identity Retrieved: {user_id}")  # Debugging line

    # Fetch notifications for the current user
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.timestamp.desc()).all()
    print(f"DEBUG: Notifications Retrieved: {notifications}")  # Debugging line

    if not notifications:
        return jsonify({"message": "No notifications found"}), 404

    return jsonify([
        {"id": n.id, "message": n.message, "timestamp": n.timestamp.strftime('%Y-%m-%d %H:%M:%S')} for n in notifications
    ]), 200