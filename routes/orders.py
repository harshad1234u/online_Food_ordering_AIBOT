from flask import Blueprint, jsonify, request, session
from models.order import Order
from models.food import Food

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/', methods=['POST'])
def place_order():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
        
    cart = session.get('cart', {})
    if not cart:
        return jsonify({"error": "Cart is empty"}), 400
        
    cart_items = []
    total_price = 0
    
    for food_id, quantity in cart.items():
        food = Food.get_by_id(int(food_id))
        if food:
            item_total = float(food['price']) * quantity
            total_price += item_total
            cart_items.append({
                'food_id': int(food_id),
                'quantity': quantity,
                'price': float(food['price'])
            })
            
    order_id = Order.create_order(user_id, cart_items, total_price)
    
    if order_id:
        session['cart'] = {} # Clear cart
        session.modified = True
        return jsonify({"message": "Order placed successfully", "order_id": order_id}), 201
    else:
        return jsonify({"error": "Failed to place order"}), 500

@orders_bp.route('/', methods=['GET'])
def get_orders():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
        
    orders = Order.get_by_user(user_id)
    return jsonify(orders), 200
