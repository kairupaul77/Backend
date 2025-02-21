from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Notification, db
from utils.pagination import paginate

notification_bp = Blueprint('notification_bp', __name__, )

# Route to get notifications with pagination
@notification_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    
    # Query notifications based on user_id
    query = Notification.query.filter_by(user_id=user_id)
    
    # Apply pagination utility
    return paginate(query, Notification)

# Route to mark notifications as read
@notification_bp.route('/mark_read', methods=['POST'])
@jwt_required()
def mark_notifications_as_read():
    user_id = get_jwt_identity()
    notification_ids = request.json.get('notification_ids', [])
    
    # Find notifications by ids
    notifications = Notification.query.filter(Notification.id.in_(notification_ids), Notification.user_id == user_id).all()
    
    if not notifications:
        return jsonify({"error": "No notifications found"}), 404
    
    # Mark notifications as read
    for notification in notifications:
        notification.is_read = True
    
    db.session.commit()
    return jsonify({"message": "Notifications marked as read."}), 200