from database import get_db_connection

class Order:
    @staticmethod
    def create_order(user_id, cart_items, total_price):
        conn = get_db_connection()
        if not conn: return None
        cursor = conn.cursor()
        
        try:
            # Create order record
            cursor.execute(
                "INSERT INTO orders (user_id, total_price, status) VALUES (%s, %s, %s)",
                (user_id, total_price, 'Pending')
            )
            order_id = cursor.lastrowid
            
            # Create order items
            for item in cart_items:
                cursor.execute(
                    "INSERT INTO order_items (order_id, food_id, quantity, price) VALUES (%s, %s, %s, %s)",
                    (order_id, item['food_id'], item['quantity'], item['price'])
                )
                
            conn.commit()
            return order_id
        except Exception as e:
            print(f"Error creating order: {e}")
            conn.rollback()
            return None
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def get_by_user(user_id):
        conn = get_db_connection()
        if not conn: return []
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY order_date DESC", (user_id,))
        orders = cursor.fetchall()
        
        # Get items for each order
        for order in orders:
            cursor.execute("""
                SELECT oi.quantity, oi.price, f.name, f.image_url 
                FROM order_items oi 
                JOIN food_items f ON oi.food_id = f.food_id 
                WHERE oi.order_id = %s
            """, (order['order_id'],))
            order['items'] = cursor.fetchall()
            
        cursor.close()
        conn.close()
        return orders

    @staticmethod
    def get_all():
        conn = get_db_connection()
        if not conn: return []
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT o.*, u.name as user_name, u.email 
            FROM orders o 
            JOIN users u ON o.user_id = u.user_id 
            ORDER BY o.order_date DESC
        """)
        orders = cursor.fetchall()
        cursor.close()
        conn.close()
        return orders
