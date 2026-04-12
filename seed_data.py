import mysql.connector
import bcrypt
from database import get_db_connection

def seed():
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()

    # Create admin user
    hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('''
        INSERT IGNORE INTO users (name, email, password, phone, address, is_admin)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', ('Admin User', 'admin@foodie.com', hashed_password, '1234567890', 'Admin HQ', True))

    # Sample food items (5 per category)
    foods = [
        # Indian
        ('Chicken Biryani', 'Indian', 350.00, 'Authentic spicy chicken biryani with raita', 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?q=80&w=600&auto=format&fit=crop'),
        ('Butter Chicken', 'Indian', 400.00, 'Creamy and rich tomato-based chicken curry', 'https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?q=80&w=600&auto=format&fit=crop'),
        ('Palak Paneer', 'Indian', 320.00, 'Cottage cheese cubes in a thick spinach gravy', 'https://images.unsplash.com/photo-1601050690597-df0568f70950?q=80&w=600&auto=format&fit=crop'),
        ('Masala Dosa', 'Indian', 180.00, 'Crispy rice crepe filled with spiced potatoes', 'https://images.unsplash.com/photo-1627308595229-7830f5c92f44?q=80&w=600&auto=format&fit=crop'),
        ('Samosa Chaat', 'Indian', 120.00, 'Crushed samosas topped with yogurt and chutneys', 'https://images.unsplash.com/photo-1601050690117-94f5f6af8bdx?q=80&w=600&auto=format&fit=crop'),
        
        # Italian
        ('Margherita Pizza', 'Italian', 450.00, 'Classic pizza with fresh mozzarella and basil', 'https://images.unsplash.com/photo-1604068549290-dea0e4a30536?q=80&w=600&auto=format&fit=crop'),
        ('Spaghetti Carbonara', 'Italian', 550.00, 'Pasta with creamy egg sauce, pancetta, and pecorino', 'https://images.unsplash.com/photo-1612874742237-6526221588e3?q=80&w=600&auto=format&fit=crop'),
        ('Lasagna', 'Italian', 500.00, 'Layered pasta with rich meat sauce and cheese', 'https://images.unsplash.com/photo-1574894709920-11b28e7367e3?q=80&w=600&auto=format&fit=crop'),
        ('Mushroom Risotto', 'Italian', 480.00, 'Creamy arborio rice with earthy mushrooms', 'https://images.unsplash.com/photo-1633964913295-ceb43826e7cf?q=80&w=600&auto=format&fit=crop'),
        ('Tiramisu', 'Italian', 250.00, 'Coffee-flavored Italian dessert', 'https://images.unsplash.com/photo-1571115177098-24ec42ed204d?q=80&w=600&auto=format&fit=crop'),

        # American
        ('Double Cheeseburger', 'American', 350.00, 'Juicy beef patty with double cheese and fries', 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?q=80&w=600&auto=format&fit=crop'),
        ('BBQ Ribs', 'American', 850.00, 'Slow-cooked pork ribs with smoky BBQ sauce', 'https://images.unsplash.com/photo-1544025162-8356fd62858b?q=80&w=600&auto=format&fit=crop'),
        ('Mac and Cheese', 'American', 300.00, 'Classic creamy and cheesy macaroni', 'https://images.unsplash.com/photo-1612871633458-958514d7c07b?q=80&w=600&auto=format&fit=crop'),
        ('Buffalo Wings', 'American', 400.00, 'Spicy fried chicken wings with blue cheese dip', 'https://images.unsplash.com/photo-1524114664604-cd8133cd67bf?q=80&w=600&auto=format&fit=crop'),
        ('Apple Pie', 'American', 200.00, 'Traditional sweet pie with spiced apple filling', 'https://images.unsplash.com/photo-1568571780765-9276ac8b75a2?q=80&w=600&auto=format&fit=crop'),

        # Asian
        ('Spicy Noodles', 'Asian', 300.00, 'Hot and spicy ramen noodles with egg', 'https://images.unsplash.com/photo-1552611052-33e04de081de?q=80&w=600&auto=format&fit=crop'),
        ('Sushi Platter', 'Asian', 1200.00, 'Assorted fresh sushi and sashimi rolls', 'https://images.unsplash.com/photo-1579871494447-9811cf80d66c?q=80&w=600&auto=format&fit=crop'),
        ('Pad Thai', 'Asian', 450.00, 'Thai stir-fried rice noodles with peanuts and shrimp', 'https://images.unsplash.com/photo-1559314809-0d155014e29e?q=80&w=600&auto=format&fit=crop'),
        ('Dim Sum', 'Asian', 400.00, 'Variety of steamed dumplings and buns', 'https://images.unsplash.com/photo-1496116218417-1a781b1c416c?q=80&w=600&auto=format&fit=crop'),
        ('Peking Duck', 'Asian', 1500.00, 'Crispy roasted duck served with pancakes and hoisin', 'https://images.unsplash.com/photo-1541696432-82c6da8ce7bf?q=80&w=600&auto=format&fit=crop'),

        # Mexican
        ('Beef Tacos', 'Mexican', 320.00, 'Crispy corn tortillas filled with seasoned beef', 'https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?q=80&w=600&auto=format&fit=crop'),
        ('Chicken Enchiladas', 'Mexican', 400.00, 'Rolled tortillas baked in chili sauce and cheese', 'https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?q=80&w=600&auto=format&fit=crop'),
        ('Guacamole & Chips', 'Mexican', 250.00, 'Freshly mashed avocados with tortilla chips', 'https://images.unsplash.com/photo-1536622432034-783bf6cd93ca?q=80&w=600&auto=format&fit=crop'),
        ('Fajitas', 'Mexican', 450.00, 'Sizzling grilled meat and peppers with tortillas', 'https://images.unsplash.com/photo-1564834724105-918b73d1b9e0?q=80&w=600&auto=format&fit=crop'),
        ('Churros', 'Mexican', 180.00, 'Fried dough pastries dusted with cinnamon sugar', 'https://images.unsplash.com/photo-1624371414361-e670eadb415a?q=80&w=600&auto=format&fit=crop')
    ]

    for f in foods:
        cursor.execute('INSERT INTO food_items (name, category, price, description, image_url) VALUES (%s, %s, %s, %s, %s)', f)

    conn.commit()
    cursor.close()
    conn.close()
    print("Database seeded successfully!")

if __name__ == '__main__':
    seed()
