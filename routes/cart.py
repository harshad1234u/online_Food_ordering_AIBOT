from flask import Blueprint, jsonify, request, session
from models.food import Food

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/', methods=['GET'])
def get_cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for food_id, quantity in cart.items():
        food = Food.get_by_id(int(food_id))
        if food:
            item_total = float(food['price']) * quantity
            total += item_total
            cart_items.append({
                'food_id': food['food_id'],
                'name': food['name'],
                'price': float(food['price']),
                'quantity': quantity,
                'image_url': food['image_url'],
                'item_total': item_total
            })
            
    return jsonify({'items': cart_items, 'total': round(total, 2)}), 200

@cart_bp.route('/add', methods=['POST'])
def add_to_cart():
    data = request.json
    food_id = str(data.get('food_id'))
    quantity = int(data.get('quantity', 1))
    
    cart = session.get('cart', {})
    
    if food_id in cart:
        cart[food_id] += quantity
    else:
        cart[food_id] = quantity
        
    session['cart'] = cart
    session.modified = True
    
    return jsonify({"message": "Added to cart", "cart_count": sum(cart.values())}), 200

@cart_bp.route('/update', methods=['POST'])
def update_cart():
    data = request.json
    food_id = str(data.get('food_id'))
    quantity = int(data.get('quantity', 0))
    
    cart = session.get('cart', {})
    
    if quantity <= 0:
        if food_id in cart:
            del cart[food_id]
    else:
        cart[food_id] = quantity
        
    session['cart'] = cart
    session.modified = True
    
    return jsonify({"message": "Cart updated", "cart_count": sum(cart.values())}), 200

@cart_bp.route('/remove', methods=['POST'])
def remove_from_cart():
    data = request.json
    food_id = str(data.get('food_id'))
    
    cart = session.get('cart', {})
    if food_id in cart:
        del cart[food_id]
        
    session['cart'] = cart
    session.modified = True
    
    return jsonify({"message": "Removed from cart", "cart_count": sum(cart.values())}), 200

@cart_bp.route('/clear', methods=['POST'])
def clear_cart():
    session['cart'] = {}
    session.modified = True
    return jsonify({"message": "Cart cleared"}), 200
