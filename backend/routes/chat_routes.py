from flask import Blueprint, request, jsonify, g
from extensions import db
from models.models import ChatMessage, Doctor
from datetime import datetime

chat_bp = Blueprint('chat_bp', __name__)

@chat_bp.route('/send', methods=['POST'])
def send_message():
    if not g.user:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401
    
    data = request.get_json() or {}
    receiver_role = (data.get('receiver_role') or '').strip().lower()
    receiver_id = int(data.get('receiver_id') or 0)
    content = data.get('content')

    if not receiver_role or not receiver_id or not content:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    sender_role = getattr(g.user, 'role', 'patient').strip().lower()
    sender_id = int(g.user.id)

    print(f"CHAT SEND: From {sender_role}({sender_id}) TO {receiver_role}({receiver_id})")
    
    # Enforcement
    if not ((sender_role == 'admin' and receiver_role == 'doctor') or 
            (sender_role == 'doctor' and receiver_role == 'admin')):
        print(f"CHAT BLOCKED: {sender_role} -> {receiver_role}")
        return jsonify({"status": "error", "message": "Unauthorized chat roles"}), 403

    msg = ChatMessage(
        sender_role=sender_role,
        sender_id=sender_id,
        receiver_role=receiver_role,
        receiver_id=receiver_id,
        content=content
    )
    db.session.add(msg)
    db.session.commit()
    
    return jsonify({"status": "success", "message": msg.to_dict()})

@chat_bp.route('/history/<other_role>/<int:other_id>', methods=['GET'])
def get_history(other_role, other_id):
    if not g.user:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401
    
    my_role = getattr(g.user, 'role', 'patient').strip().lower()
    my_id = int(g.user.id)
    other_role = other_role.strip().lower()
    other_id_val = int(other_id)

    print(f"CHAT HISTORY: {my_role}({my_id}) WITH {other_role}({other_id_val})")

    messages = ChatMessage.query.filter(
        (
            (ChatMessage.sender_role == my_role) & 
            (ChatMessage.sender_id == my_id) & 
            (ChatMessage.receiver_role == other_role) & 
            (ChatMessage.receiver_id == other_id_val)
        ) | (
            (ChatMessage.sender_role == other_role) & 
            (ChatMessage.sender_id == other_id_val) & 
            (ChatMessage.receiver_role == my_role) & 
            (ChatMessage.receiver_id == my_id)
        )
    ).order_by(ChatMessage.timestamp.asc()).all()

    # Mark as read
    ChatMessage.query.filter(
        ChatMessage.sender_role == other_role,
        ChatMessage.sender_id == other_id_val,
        ChatMessage.receiver_role == my_role,
        ChatMessage.receiver_id == my_id,
        ChatMessage.is_read == False
    ).update({"is_read": True})
    db.session.commit()

    return jsonify({"status": "success", "messages": [m.to_dict() for m in messages]})

@chat_bp.route('/conversations', methods=['GET'])
def get_conversations():
    if not g.user:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401
    
    from models.admin import Admin
    my_role = getattr(g.user, 'role', 'patient').strip().lower()
    my_id = int(g.user.id)
    
    def get_unread_count(other_role, other_id):
        other_role = other_role.strip().lower()
        return ChatMessage.query.filter(
            ChatMessage.sender_role == other_role,
            ChatMessage.sender_id == int(other_id),
            ChatMessage.receiver_role == my_role,
            ChatMessage.receiver_id == my_id,
            ChatMessage.is_read == False
        ).count()

    if my_role == 'admin':
        doctors = Doctor.query.filter(Doctor.status != 'deleted').all()
        return jsonify({
            "status": "success", 
            "conversations": [{
                "id": d.id, 
                "name": d.name, 
                "role": "doctor", 
                "unread_count": get_unread_count("doctor", d.id)
            } for d in doctors]
        })
    elif my_role == 'doctor':
        # Now correctly queries the dedicated Admin table
        admin = Admin.query.first()
        if admin:
            return jsonify({
                "status": "success",
                "conversations": [{
                    "id": admin.id, 
                    "name": admin.name, 
                    "role": "admin",
                    "unread_count": get_unread_count("admin", admin.id)
                }]
            })
        return jsonify({"status": "success", "conversations": []})
    
    return jsonify({"status": "error", "message": "Unauthorized"}), 403

@chat_bp.route('/unread-total', methods=['GET'])
def get_unread_total():
    if not g.user:
        return jsonify({"status": "error", "message": "Not authenticated"}), 401
    
    my_role = getattr(g.user, 'role', 'patient').strip().lower()
    my_id = int(g.user.id)
    
    count = ChatMessage.query.filter(
        ChatMessage.receiver_role == my_role,
        ChatMessage.receiver_id == my_id,
        ChatMessage.is_read == False
    ).count()
    
    return jsonify({"status": "success", "count": count})
