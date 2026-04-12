from flask import Blueprint, jsonify, request, session
from database import get_db_connection
from models.order import Order

admin_bp = Blueprint('admin', __name__)

def is_admin():
    return session.get('is_admin', False)

@admin_bp.before_request
def check_admin():
    if not is_admin():
        return jsonify({"error": "Unauthorized"}), 403

@admin_bp.route('/foods', methods=['POST'])
def add_food():
    data = request.json
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database error"}), 500
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO food_items (name, category, price, description, image_url) VALUES (%s, %s, %s, %s, %s)",
            (data['name'], data['category'], data['price'], data.get('description', ''), data.get('image_url', ''))
        )
        conn.commit()
        return jsonify({"message": "Food item added", "food_id": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@admin_bp.route('/foods/<int:food_id>', methods=['DELETE'])
def delete_food(food_id):
    conn = get_db_connection()
    if not conn: return jsonify({"error": "Database error"}), 500
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM food_items WHERE food_id = %s", (food_id,))
        conn.commit()
        return jsonify({"message": "Food item deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@admin_bp.route('/orders', methods=['GET'])
def get_all_orders():
    orders = Order.get_all()
    return jsonify(orders), 200
