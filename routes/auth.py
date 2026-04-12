from flask import Blueprint, jsonify, request, session
import bcrypt
from models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone', '')
    address = data.get('address', '')
    
    if not name or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400
        
    # Check if user exists
    existing_user = User.get_by_email(email)
    if existing_user:
        return jsonify({"error": "Email already exists"}), 400
        
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user_id = User.create(name, email, hashed_pw, phone, address)
    if user_id:
        return jsonify({"message": "Registration successful"}), 201
    else:
        return jsonify({"error": "Failed to register"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    user = User.get_by_email(email)
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({"error": "Invalid email or password"}), 401
        
    session['user_id'] = user['user_id']
    session['is_admin'] = user['is_admin']
    
    return jsonify({
        "message": "Login successful",
        "user": {
            "user_id": user['user_id'],
            "name": user['name'],
            "is_admin": user['is_admin']
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200

@auth_bp.route('/me', methods=['GET'])
def get_me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
        
    user = User.get_by_id(user_id)
    if user:
        return jsonify(user), 200
    return jsonify({"error": "User not found"}), 404
