from flask import Blueprint, jsonify, request
from models.food import Food

menu_bp = Blueprint('menu', __name__)

@menu_bp.route('/', methods=['GET'])
def get_menu():
    category = request.args.get('category')
    search = request.args.get('search')
    
    foods = Food.get_all(category, search)
    return jsonify(foods), 200

@menu_bp.route('/<int:food_id>', methods=['GET'])
def get_food(food_id):
    food = Food.get_by_id(food_id)
    if food:
        return jsonify(food), 200
    return jsonify({"error": "Food not found"}), 404

@menu_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Food.get_categories()
    return jsonify(categories), 200
