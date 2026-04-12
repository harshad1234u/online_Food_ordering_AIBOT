from flask import Flask, jsonify, render_template, session, redirect, url_for
from config import Config
from database import get_db_connection
import os
import secrets

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure secret key is random if dev default
    if app.config['SECRET_KEY'] == 'my_secure_dev_key_123':
        app.config['SECRET_KEY'] = secrets.token_hex(16)

    # Register Blueprints here later
    from routes.auth import auth_bp
    from routes.menu import menu_bp
    from routes.cart import cart_bp
    from routes.orders import orders_bp
    from routes.admin import admin_bp
    from routes.chatbot import chatbot_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(menu_bp, url_prefix='/api/menu')
    app.register_blueprint(cart_bp, url_prefix='/api/cart')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/menu')
    def menu_page():
        return render_template('menu.html')

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/cart')
    def cart_page():
        return render_template('cart.html')

    @app.route('/orders')
    def orders_page():
        return render_template('orders.html')

    @app.route('/admin')
    def admin_page():
        return render_template('admin.html')
        
    @app.route('/payment')
    def payment_page():
        return render_template('payment.html')
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
