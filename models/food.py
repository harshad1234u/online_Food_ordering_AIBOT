from database import get_db_connection
import os

def _process_image_url(food):
    if not food:
        return food
        
    img = food.get('image_url')
    if not img:
        food['image_url'] = '/static/images/default_food.png'
        return food
        
    if img.startswith('http://') or img.startswith('https://') or img.startswith('/static/'):
        return food
        
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_path = os.path.join(base_dir, 'static', 'images', img)
    if os.path.exists(local_path):
        food['image_url'] = f'/static/images/{img}'
    else:
        food['image_url'] = '/static/images/default_food.png'
        
    return food

class Food:
    @staticmethod
    def get_all(category=None, search=None):
        conn = get_db_connection()
        if not conn: return []
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT * FROM food_items WHERE 1=1"
        params = []
        
        if category:
            query += " AND category = %s"
            params.append(category)
        if search:
            query += " AND (name LIKE %s OR description LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
            
        cursor.execute(query, tuple(params))
        foods = cursor.fetchall()
        cursor.close()
        conn.close()
        
        for f in foods:
            _process_image_url(f)
            
        return foods

    @staticmethod
    def get_by_id(food_id):
        conn = get_db_connection()
        if not conn: return None
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM food_items WHERE food_id = %s", (food_id,))
        food = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return _process_image_url(food)

    @staticmethod
    def get_categories():
        conn = get_db_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM food_items")
        categories = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return categories
