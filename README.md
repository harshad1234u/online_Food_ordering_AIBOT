# Food Ordering App

A Flask-based food ordering web application with MySQL persistence, session-based cart management, admin food management, order history, and a chatbot assistant for menu browsing and ordering help.

## Features

- User registration, login, logout, and profile lookup
- Browse menu items with category and search filtering
- Add, update, remove, and clear cart items using server-side sessions
- Place orders and view order history
- Admin-only food item management and order overview
- Chatbot assistant with natural-language ordering support
- Responsive HTML templates with custom CSS and JavaScript

## Tech Stack

- Python 3
- Flask
- MySQL
- mysql-connector-python
- bcrypt
- python-dotenv
- OpenAI SDK for the chatbot integration

## Project Structure

```text
food_ordering/
  app.py
  config.py
  database.py
  init_db.py
  schema.sql
  requirements.txt
  models/
  routes/
  static/
  templates/
```

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root if needed:

```env
SECRET_KEY=your_secret_key
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=root
DB_NAME=food_ordering_db
NVIDIA_API_KEY=your_optional_nvidia_api_key
```

If `SECRET_KEY` is not set, the app uses a default development value and then replaces it with a random key at runtime.

### 4. Initialize the database

Make sure MySQL is running, then create the schema and tables:

```bash
python init_db.py
```

This reads `schema.sql`, creates the `food_ordering_db` database, and sets up the `users`, `food_items`, `orders`, and `order_items` tables.

### 5. Run the app

```bash
python app.py
```

By default, the app runs in debug mode and serves pages such as `/`, `/menu`, `/cart`, `/orders`, `/admin`, and `/payment`.

## Main API Routes

### Auth

- `POST /api/register` - register a new user
- `POST /api/login` - log in a user
- `POST /api/logout` - log out the current session
- `GET /api/me` - fetch the logged-in user

### Menu

- `GET /api/menu/` - list menu items
- `GET /api/menu/<food_id>` - get a single food item
- `GET /api/menu/categories` - list available categories

### Cart

- `GET /api/cart/` - get cart contents
- `POST /api/cart/add` - add an item
- `POST /api/cart/update` - update quantity
- `POST /api/cart/remove` - remove an item
- `POST /api/cart/clear` - clear the cart

### Orders

- `POST /api/orders/` - place an order
- `GET /api/orders/` - view the current user's orders

### Admin

- `POST /api/admin/foods` - add a food item
- `DELETE /api/admin/foods/<food_id>` - delete a food item
- `GET /api/admin/orders` - view all orders

### Chatbot

- `POST /api/chatbot/` - chat with the ordering assistant

## Notes

- Admin access is controlled through the `is_admin` flag in the `users` table.
- Cart data is stored in the Flask session.
- Food image paths can be local files in `static/images/` or external URLs.
- The chatbot can fall back to rule-based behavior if an AI key is not configured.

## License

No license file is included in this project.