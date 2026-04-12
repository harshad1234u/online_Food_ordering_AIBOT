import os
import json
import re
from flask import Blueprint, jsonify, request, session
from models.food import Food

chatbot_bp = Blueprint('chatbot', __name__)

NVIDIA_API_KEY = os.environ.get('NVIDIA_API_KEY')
use_ai = False

try:
    from openai import OpenAI
    if NVIDIA_API_KEY and len(NVIDIA_API_KEY) > 10:
        client = OpenAI(
            api_key=NVIDIA_API_KEY,
            base_url="https://integrate.api.nvidia.com/v1"
        )
        use_ai = True
except Exception as e:
    print(f"NVIDIA API configuration error: {e}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_food_lookup(foods):
    """Build a dict mapping food_id -> food dict for fast lookups."""
    return {f['food_id']: f for f in foods}


def _parse_quantity(text):
    """Extract a numeric quantity from text. Defaults to 1."""
    m = re.search(r'(\d+)', text)
    return int(m.group(1)) if m else 1


def _fuzzy_find_food(name_fragment, foods):
    """Find a food item whose name best matches the fragment (case-insensitive)."""
    name_fragment = name_fragment.lower().strip()
    # Exact substring match first
    for f in foods:
        if name_fragment in f['name'].lower():
            return f
    # Word-overlap score
    target_words = set(name_fragment.split())
    best, best_score = None, 0
    for f in foods:
        food_words = set(f['name'].lower().split())
        score = len(target_words & food_words)
        if score > best_score:
            best, best_score = f, score
    return best if best_score > 0 else None


def _safe_image(food):
    """Return a safe image URL with fallback."""
    img = food.get('image_url', '')
    if not img or img == 'None':
        return '/static/images/default_food.png'
    if img.startswith('http://') or img.startswith('https://') or img.startswith('/static/'):
        return img
    # Try local file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_path = os.path.join(base_dir, 'static', 'images', img)
    if os.path.exists(local_path):
        return f'/static/images/{img}'
    return '/static/images/default_food.png'


def _food_card(food):
    """Build a structured food card dict for frontend rendering."""
    return {
        'food_id': food['food_id'],
        'name': food['name'],
        'price': float(food['price']),
        'image': _safe_image(food),
        'description': food.get('description', ''),
        'category': food.get('category', ''),
    }


def _cart_summary(cart, foods):
    """Build a detailed cart summary with total price."""
    lookup = _build_food_lookup(foods)
    items = []
    total = 0
    for fid_str, qty in cart.items():
        fid = int(fid_str)
        f = lookup.get(fid)
        if f:
            item_total = float(f['price']) * qty
            total += item_total
            items.append({
                'food_id': f['food_id'],
                'name': f['name'],
                'price': float(f['price']),
                'quantity': qty,
                'item_total': round(item_total, 2),
                'image': _safe_image(f),
            })
    return items, round(total, 2)


# ---------------------------------------------------------------------------
# Emoji helpers for modern personality
# ---------------------------------------------------------------------------

CATEGORY_EMOJIS = {
    'Indian': '🍛', 'Italian': '🍕', 'American': '🍔',
    'Asian': '🥢', 'Mexican': '🌮',
}

TASTE_EMOJIS = {
    'spicy': '🔥', 'sweet': '🍰', 'creamy': '🧈',
    'cheesy': '🧀', 'healthy': '🥗', 'vegetarian': '🥗',
    'veg': '🥗', 'non-veg': '🍗', 'cheap': '💰', 'budget': '💰',
}


def _pick_emoji(message):
    """Pick a fitting emoji based on message keywords."""
    msg = message.lower()
    for kw, emoji in TASTE_EMOJIS.items():
        if kw in msg:
            return emoji
    for kw, emoji in CATEGORY_EMOJIS.items():
        if kw.lower() in msg:
            return emoji
    return '✨'


# ---------------------------------------------------------------------------
# Improved fallback engine (no AI needed)
# ---------------------------------------------------------------------------

# Patterns for natural ordering detection
ORDER_PATTERNS = [
    re.compile(r"(?:i(?:'ll| will)?\s+(?:take|have|get|order))\s+(.+)", re.I),
    re.compile(r"(?:(?:can you |please )?(?:add|order|give|get|bring)(?:\s+me)?)\s+(.+)", re.I),
    re.compile(r"(?:put)\s+(.+?)(?:\s+in (?:my )?cart)", re.I),
    re.compile(r"(?:buy)\s+(.+)", re.I),
]

# "I want" is SEPARATE — only treated as order if the rest matches a specific food name
WANT_ORDER_PATTERN = re.compile(
    r"(?:i\s+want)\s+(\d+\s+)?(.+)", re.I
)

AFFIRM_PATTERNS = re.compile(
    r"^(?:ok(?:ay)?|yes|yeah|yep|yup|sure|do it|go ahead|add (?:it|that|this)|"
    r"i(?:'ll| will)? (?:add|take|have|want) (?:it|that|this)|that (?:one|sounds good)|"
    r"sounds good|perfect|great|let'?s do it)\.?!?$",
    re.I
)

SHOW_MENU_PATTERNS = re.compile(
    r"(?:show|see|view|open|display|browse|what'?s on)\s*(?:the )?\s*menu|"
    r"(?:what do you (?:have|serve|offer))|(?:menu\s*(?:please)?$)",
    re.I
)

SHOW_CART_PATTERNS = re.compile(
    r"(?:show|see|view|open|what'?s in)\s*(?:my )?\s*cart|"
    r"(?:my cart|my order(?:s)?$)",
    re.I
)

BILL_PATTERNS = re.compile(
    r"(?:total|bill|how much|price|cost|amount|what (?:do i|will i|would i) (?:owe|pay))|"
    r"(?:cart total|order total|my total|what is (?:the )?total|final (?:bill|price|amount))",
    re.I
)

CHECKOUT_PATTERNS = re.compile(
    r"(?:check\s*out|pay(?:ment)?|place\s*(?:my )?order|proceed|done ordering|"
    r"i(?:'m| am) (?:done|ready|finished)|complete (?:my )?order|finish)",
    re.I
)

PAYMENT_PATTERNS = re.compile(
    r"(?:how (?:do i|can i|to) pay|payment (?:method|option)s?|"
    r"(?:do you )?(?:accept|take) (?:upi|card|cash|cod))",
    re.I
)

GREETING_PATTERNS = re.compile(
    r"^(?:hi|hello|hey|howdy|good (?:morning|afternoon|evening)|yo|sup|what'?s up)[\s!?.]*$",
    re.I
)

REMOVE_PATTERNS = re.compile(
    r"(?:remove|delete|drop|take out|cancel)\s+(.+?)(?:\s+from (?:my )?cart)?$",
    re.I
)

RECOMMEND_PATTERNS = re.compile(
    r"(?:suggest|recommend|what should i|any (?:good|popular)|"
    r"i(?:'m| am) (?:hungry|looking for|in the mood)|"
    r"something|anything|what'?s (?:good|popular|best|special))",
    re.I
)

# --- NEW: broader "want" / preference intent (NOT direct ordering) ---
WANT_PATTERNS = re.compile(
    r"(?:i (?:want|need|crave|feel like)|(?:craving|looking for|in the mood for))\s+(?:something\s+)?"
    r"(spicy|sweet|creamy|cheesy|healthy|veg|vegetarian|non[- ]?veg|indian|italian|american|asian|mexican|"
    r"cheap|budget|affordable|dessert|breakfast|lunch|dinner|snack)",
    re.I
)

MEAL_KEYWORDS = {
    'breakfast': ['masala dosa', 'samosa chaat', 'dim sum'],
    'lunch': ['chicken biryani', 'butter chicken', 'margherita pizza', 'pad thai', 'beef tacos'],
    'dinner': ['bbq ribs', 'lasagna', 'peking duck', 'spaghetti carbonara', 'fajitas'],
    'dessert': ['tiramisu', 'apple pie', 'churros'],
    'snack': ['samosa chaat', 'buffalo wings', 'guacamole & chips', 'churros'],
}

TASTE_KEYWORDS = {
    'spicy': ['chicken biryani', 'spicy noodles', 'buffalo wings', 'beef tacos', 'masala dosa'],
    'sweet': ['tiramisu', 'apple pie', 'churros'],
    'creamy': ['butter chicken', 'mac and cheese', 'mushroom risotto', 'palak paneer'],
    'cheesy': ['margherita pizza', 'double cheeseburger', 'mac and cheese', 'lasagna'],
    'vegetarian': ['palak paneer', 'masala dosa', 'margherita pizza', 'mushroom risotto', 'mac and cheese', 'guacamole & chips'],
    'veg': ['palak paneer', 'masala dosa', 'margherita pizza', 'mushroom risotto', 'mac and cheese', 'guacamole & chips'],
    'non-veg': ['chicken biryani', 'butter chicken', 'bbq ribs', 'double cheeseburger', 'peking duck', 'sushi platter'],
    'nonveg': ['chicken biryani', 'butter chicken', 'bbq ribs', 'double cheeseburger', 'peking duck', 'sushi platter'],
    'healthy': ['pad thai', 'sushi platter', 'palak paneer', 'guacamole & chips'],
}

CATEGORY_ALIASES = {
    'indian': 'Indian', 'desi': 'Indian',
    'italian': 'Italian', 'pasta': 'Italian', 'pizza': 'Italian',
    'american': 'American', 'burger': 'American',
    'asian': 'Asian', 'chinese': 'Asian', 'japanese': 'Asian', 'thai': 'Asian',
    'mexican': 'Mexican', 'taco': 'Mexican',
}

# Price tiers for "cheap"/"budget"/"affordable" queries
PRICE_KEYWORDS = {
    'cheap': (0, 250),
    'budget': (0, 250),
    'affordable': (0, 300),
    'expensive': (500, 99999),
    'premium': (500, 99999),
    'luxury': (800, 99999),
}


def _get_recommendations(message, foods, limit=5):
    """Return a list of food items matching taste/meal/category/price keywords."""
    msg = message.lower()
    matched_names = set()
    matched_foods = []

    # Check price keywords FIRST
    for keyword, (lo, hi) in PRICE_KEYWORDS.items():
        if keyword in msg:
            price_matches = [f for f in foods if lo <= float(f['price']) <= hi]
            price_matches.sort(key=lambda f: float(f['price']))
            return price_matches[:limit]

    # Check taste keywords (including "veg" alias)
    for keyword, names in TASTE_KEYWORDS.items():
        if keyword in msg:
            matched_names.update(names)

    # Check meal keywords
    for keyword, names in MEAL_KEYWORDS.items():
        if keyword in msg:
            matched_names.update(names)

    # Check category aliases
    for alias, category in CATEGORY_ALIASES.items():
        if alias in msg:
            for f in foods:
                if f['category'] == category:
                    matched_names.add(f['name'].lower())

    if matched_names:
        results = [f for f in foods if f['name'].lower() in matched_names]
        return results[:limit]

    # Fallback: search in name + description
    words = [w for w in msg.split() if len(w) > 2 and w not in ('the', 'and', 'for', 'some', 'food', 'want', 'give', 'suggest', 'something', 'anything')]
    if words:
        scored = []
        for f in foods:
            text = f"{f['name']} {f.get('description', '')} {f.get('category', '')}".lower()
            score = sum(1 for w in words if w in text)
            if score > 0:
                scored.append((score, f))
        scored.sort(key=lambda x: -x[0])
        if scored:
            return [f for _, f in scored[:limit]]

    return []


# ---------------------------------------------------------------------------
# Response builders (structured JSON for modern UI)
# ---------------------------------------------------------------------------

def _text_response(reply, action="none", food_id=None, quantity=0):
    """Build a text-only response."""
    return {
        "type": "text",
        "reply": reply,
        "action": action,
        "food_id": food_id,
        "quantity": quantity,
        "data": [],
    }


def _list_response(reply, foods_list, action="recommend", food_id=None):
    """Build a food-card-list response."""
    cards = [_food_card(f) for f in foods_list]
    return {
        "type": "list",
        "reply": reply,
        "action": action,
        "food_id": food_id or (foods_list[0]['food_id'] if foods_list else None),
        "quantity": 0,
        "data": cards,
    }


def _cart_response(reply, cart_items, total, action="show_cart"):
    """Build a cart-summary response."""
    return {
        "type": "cart",
        "reply": reply,
        "action": action,
        "food_id": None,
        "quantity": 0,
        "data": cart_items,
        "cart_total": total,
    }


def _added_response(food, qty=1):
    """Build a response confirming item was added."""
    return {
        "type": "added",
        "reply": f"✅ {qty}x {food['name']} (₹{float(food['price']):.0f}) added to your cart!",
        "action": "add_to_cart",
        "food_id": food['food_id'],
        "quantity": qty,
        "data": [_food_card(food)],
    }


# ---------------------------------------------------------------------------
# Main fallback response engine
# ---------------------------------------------------------------------------

def get_fallback_response(message, foods):
    """Improved fallback that handles many natural language patterns."""
    message = message.strip()
    msg_lower = message.lower()
    cart = session.get('cart', {})

    # --- Greetings ---
    if GREETING_PATTERNS.match(message):
        return _text_response(
            "👋 Hey there! I'm your AI food assistant. Ask me to suggest something, or just say what you're craving! 🍽️"
        )

    # --- "Add it / that / this" → use last recommendation ---
    if AFFIRM_PATTERNS.match(message):
        last = session.get('chatbot_last_recommended')
        if last:
            food = next((f for f in foods if f['food_id'] == last['food_id']), None)
            if food:
                return _added_response(food)
        return _text_response(
            "🤔 Which item would you like me to add? You can say a dish name or ask me to suggest something."
        )

    # --- Show menu ---
    if SHOW_MENU_PATTERNS.search(message):
        return _text_response(
            "📋 Here's our menu! Taking you there now.", action="show_menu"
        )

    # --- Bill / total / how much ---
    if BILL_PATTERNS.search(message):
        if cart:
            items, total = _cart_summary(cart, foods)
            item_count = sum(cart.values())
            return _cart_response(
                f"🛒 You have {item_count} item{'s' if item_count != 1 else ''}. Total: ₹{total:.0f}",
                items, total
            )
        return _text_response(
            "🛒 Your cart is empty! Browse the menu or ask me for suggestions. 🍔"
        )

    # --- Show cart ---
    if SHOW_CART_PATTERNS.search(message):
        if cart:
            items, total = _cart_summary(cart, foods)
            item_count = sum(cart.values())
            return _cart_response(
                f"🛒 Here's your cart — {item_count} item{'s' if item_count != 1 else ''}, Total: ₹{total:.0f}",
                items, total
            )
        return _text_response(
            "🛒 Your cart is empty! Want me to suggest something delicious? 🍕"
        )

    # --- Payment guidance ---
    if PAYMENT_PATTERNS.search(message):
        return _text_response(
            "💳 You can pay via UPI, Credit/Debit Card, or Cash on Delivery at checkout!"
        )

    # --- Checkout / place order ---
    if CHECKOUT_PATTERNS.search(message):
        if cart:
            items, total = _cart_summary(cart, foods)
            return _text_response(
                f"🚀 Taking you to checkout! Your total is ₹{total:.0f}",
                action="place_order"
            )
        return _text_response(
            "🛒 Your cart is empty. Let me suggest something first! What are you in the mood for?"
        )

    # --- Remove item ---
    rm = REMOVE_PATTERNS.search(message)
    if rm:
        target = rm.group(1).strip()
        food = _fuzzy_find_food(target, foods)
        if food:
            return _text_response(
                f"🗑️ {food['name']} removed from your cart!",
                action="remove_from_cart",
                food_id=food['food_id'],
                quantity=999,
            )
        return _text_response(
            f"😅 Couldn't find \"{target}\" in the menu. Try the exact dish name!"
        )

    # --- "I want something spicy/veg/..." (preference, NOT direct order) ---
    want_match = WANT_PATTERNS.search(message)
    if want_match:
        preference = want_match.group(1).strip().lower()
        recs = _get_recommendations(preference, foods, limit=5)
        if not recs:
            recs = _get_recommendations(message, foods, limit=5)
        if recs:
            emoji = _pick_emoji(preference)
            session['chatbot_last_recommended'] = {'food_id': recs[0]['food_id'], 'name': recs[0]['name']}
            session.modified = True
            return _list_response(
                f"{emoji} Craving {preference}? Try these!",
                recs
            )

    # --- Order / add intent (specific food names) ---
    for pattern in ORDER_PATTERNS:
        m = pattern.search(message)
        if m:
            target = m.group(1).strip()
            qty = _parse_quantity(target)
            target_clean = re.sub(r'^\d+\s*', '', target).strip()
            food = _fuzzy_find_food(target_clean, foods)
            if food:
                return _added_response(food, qty)
            # If no food match, maybe they're asking for a category
            recs = _get_recommendations(target_clean, foods, limit=5)
            if recs:
                emoji = _pick_emoji(target_clean)
                session['chatbot_last_recommended'] = {'food_id': recs[0]['food_id'], 'name': recs[0]['name']}
                session.modified = True
                return _list_response(
                    f"{emoji} Here are some options for \"{target_clean}\":",
                    recs
                )
            return _text_response(
                f"😅 Couldn't find \"{target_clean}\" on our menu. Try asking me to suggest something!"
            )

    # --- "I want [food name]" direct order check ---
    want_m = WANT_ORDER_PATTERN.search(message)
    if want_m:
        qty_str = want_m.group(1)
        target = want_m.group(2).strip()
        qty = int(qty_str.strip()) if qty_str else 1
        food = _fuzzy_find_food(target, foods)
        if food:
            return _added_response(food, qty)
        # Not a specific food — treat as recommendation
        recs = _get_recommendations(target, foods, limit=5)
        if recs:
            emoji = _pick_emoji(target)
            session['chatbot_last_recommended'] = {'food_id': recs[0]['food_id'], 'name': recs[0]['name']}
            session.modified = True
            return _list_response(
                f"{emoji} Here's what we suggest for \"{target}\":",
                recs
            )

    # --- Recommendation intent ---
    if RECOMMEND_PATTERNS.search(message):
        recs = _get_recommendations(message, foods, limit=5)
        if not recs:
            recs = foods[:5]
        emoji = _pick_emoji(message)
        session['chatbot_last_recommended'] = {'food_id': recs[0]['food_id'], 'name': recs[0]['name']}
        session.modified = True
        return _list_response(
            f"{emoji} How about these? Tap '+' to add!",
            recs
        )

    # --- Category match (user just types "indian", "mexican", etc.) ---
    for alias, category in CATEGORY_ALIASES.items():
        if alias in msg_lower.split():
            cat_foods = [f for f in foods if f['category'] == category][:5]
            if cat_foods:
                emoji = CATEGORY_EMOJIS.get(category, '🍽️')
                session['chatbot_last_recommended'] = {'food_id': cat_foods[0]['food_id'], 'name': cat_foods[0]['name']}
                session.modified = True
                return _list_response(
                    f"{emoji} Here's our {category} selection:",
                    cat_foods
                )

    # --- Price keyword standalone ("cheap food", "budget meals") ---
    for keyword in PRICE_KEYWORDS:
        if keyword in msg_lower:
            recs = _get_recommendations(message, foods, limit=5)
            if recs:
                session['chatbot_last_recommended'] = {'food_id': recs[0]['food_id'], 'name': recs[0]['name']}
                session.modified = True
                return _list_response(
                    f"💰 Best value picks for you:",
                    recs
                )

    # --- Direct food name match (user just types "biryani", "pizza", etc.) ---
    food = _fuzzy_find_food(msg_lower, foods)
    if food:
        session['chatbot_last_recommended'] = {'food_id': food['food_id'], 'name': food['name']}
        session.modified = True
        return _list_response(
            f"🍽️ {food['name']} — ₹{float(food['price']):.0f}. {food.get('description', '')}. Add it?",
            [food],
        )

    # --- Encourage checkout if cart has items ---
    if cart:
        items, total = _cart_summary(cart, foods)
        item_count = sum(cart.values())
        return _text_response(
            f"🤖 I can help you order! You have {item_count} item{'s' if item_count != 1 else ''} (₹{total:.0f}) in your cart. Say 'suggest' or a cuisine name!"
        )

    # --- Off-topic / default redirect ---
    return _text_response(
        "🤖 I'm here to help you order delicious food! Try:\n• \"suggest something spicy 🔥\"\n• \"show me veg options 🥗\"\n• \"cheap food 💰\"\n• Or just say a dish name!"
    )


# ---------------------------------------------------------------------------
# AI system prompt (matches the user's specification)
# ---------------------------------------------------------------------------

def _build_system_prompt(foods, cart):
    menu_items = "\n".join([
        f"  - ID:{f['food_id']} | {f['name']} | {f['category']} | ₹{f['price']} | {f['description']}"
        for f in foods
    ])

    cart_summary = "empty"
    if cart:
        lookup = _build_food_lookup(foods)
        cart_lines = []
        for fid_str, qty in cart.items():
            fid = int(fid_str)
            f = lookup.get(fid)
            if f:
                cart_lines.append(f"{qty}x {f['name']} (₹{f['price']})")
        if cart_lines:
            cart_summary = ", ".join(cart_lines)

    last_rec = session.get('chatbot_last_recommended')
    last_rec_info = ""
    if last_rec:
        last_rec_info = f"\nLast recommended item: ID:{last_rec['food_id']} {last_rec['name']}. If the user says 'add it', 'ok', 'yes', 'that one', etc., add THIS item."

    return f"""You are an AI Food Ordering Assistant on the "AI Foodie" website. Your job is to help users discover food, add items to cart, and complete orders using natural conversation.

RULES:
1. You are ONLY for food ordering. If the user asks unrelated questions (jokes, trivia, personal questions), politely redirect: "I'm here to help you order delicious food! Would you like to see the menu or get a recommendation?"
2. Detect ordering intent from casual phrases like "I want pizza", "give me a burger", "add two burgers", "I'll take pasta", "order biryani".
3. If the user says "add it", "ok", "yes", "that one", "sounds good" etc., they want the last recommended item added to cart.
4. Recommend items based on category (spicy, vegetarian, dessert), meal type (breakfast, lunch, dinner), or popularity.
5. Keep responses SHORT and friendly (1-2 sentences max). Never give long explanations.
6. Always confirm when items are added: "Done! Margherita Pizza has been added to your cart."
7. If the user has items in cart, occasionally encourage checkout: "You can continue ordering or proceed to checkout."
8. Handle ambiguous commands by asking a simple follow-up: "Which item would you like me to add?"
9. For payment questions, reply: "You can complete your order on the payment page using UPI, card, or cash on delivery."
10. ONLY suggest items from the menu below. Never invent items.

MENU:
{menu_items}

CURRENT CART: {cart_summary}
{last_rec_info}

You MUST respond with a JSON object in this exact format (no extra text, no markdown):
{{
  "reply": "Your short, friendly reply",
  "action": "recommend | add_to_cart | remove_from_cart | show_menu | show_cart | place_order | none",
  "food_id": <integer ID from menu or null>,
  "quantity": <integer, default 1>
}}

ACTIONS:
- "add_to_cart": User orders/adds food. Include food_id and quantity.
- "remove_from_cart": User wants to remove an item. Include food_id, quantity=999 to remove all.
- "show_menu": User wants to browse the menu.
- "show_cart": User wants to view their cart.
- "place_order": User is ready to checkout/pay.
- "recommend": You're suggesting items. Set food_id to the first suggested item.
- "none": General conversation, guidance, or redirect.

EXAMPLES:
{{"reply": "Done! 2x Chicken Biryani added to your cart.", "action": "add_to_cart", "food_id": 1, "quantity": 2}}
{{"reply": "You might enjoy Spicy Noodles or Chicken Biryani!", "action": "recommend", "food_id": 16, "quantity": 0}}
{{"reply": "Taking you to checkout!", "action": "place_order", "food_id": null, "quantity": 0}}
{{"reply": "I'm here to help you order food! Want to see the menu?", "action": "none", "food_id": null, "quantity": 0}}"""


# ---------------------------------------------------------------------------
# Main chat endpoint
# ---------------------------------------------------------------------------

@chatbot_bp.route('/', methods=['POST'])
def chat():
    data = request.json
    message = data.get('message', '').strip()
    conversation_history = data.get('history', [])

    if not message:
        return jsonify(_text_response(
            "💬 Say something! I'm ready to help you order delicious food! 🍕"
        )), 200

    foods = Food.get_all()
    cart = session.get('cart', {})

    # --- Fallback mode (no AI) ---
    if not use_ai:
        result = get_fallback_response(message, foods)
        handle_cart_action(result)
        cart = session.get('cart', {})
        result['cart_count'] = sum(cart.values())
        _track_recommendation(result)
        return jsonify(result), 200

    # --- AI mode ---
    try:
        system_prompt = _build_system_prompt(foods, cart)

        # Build message list with conversation context (last 6 turns max)
        messages = [{"role": "system", "content": system_prompt}]
        for turn in conversation_history[-6:]:
            role = "user" if turn.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": turn.get("content", "")})
        messages.append({"role": "user", "content": message})

        response = client.chat.completions.create(
            model="google/gemma-2-9b-it",
            messages=messages,
            temperature=0.1,
            max_tokens=250,
        )
        text = response.choices[0].message.content

        # Clean up JSON
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        # Try to extract JSON from mixed output
        json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_match:
            text = json_match.group(0)

        ai_result = json.loads(text)

        # Validate food_id exists in menu
        if ai_result.get('food_id'):
            valid_ids = {f['food_id'] for f in foods}
            if ai_result['food_id'] not in valid_ids:
                ai_result['food_id'] = None
                if ai_result.get('action') in ('add_to_cart', 'remove_from_cart'):
                    ai_result['action'] = 'none'
                    ai_result['reply'] += " (I couldn't find that item — could you try again?)"

        # Convert AI plain response to structured format
        action = ai_result.get('action', 'none')
        fid = ai_result.get('food_id')

        if action == 'recommend' and fid:
            food = next((f for f in foods if f['food_id'] == fid), None)
            if food:
                # Try to get related items too
                recs = _get_recommendations(message, foods, limit=5)
                if not recs or food not in recs:
                    recs = [food] + [r for r in recs if r['food_id'] != food['food_id']][:4]
                result = _list_response(ai_result['reply'], recs[:5], food_id=fid)
            else:
                result = _text_response(ai_result['reply'], action, fid, ai_result.get('quantity', 0))
        elif action == 'add_to_cart' and fid:
            food = next((f for f in foods if f['food_id'] == fid), None)
            if food:
                result = _added_response(food, ai_result.get('quantity', 1))
            else:
                result = _text_response(ai_result['reply'], action, fid, ai_result.get('quantity', 1))
        elif action == 'show_cart':
            if cart:
                items, total = _cart_summary(cart, foods)
                item_count = sum(cart.values())
                result = _cart_response(
                    f"🛒 {item_count} item{'s' if item_count != 1 else ''} in your cart. Total: ₹{total:.0f}",
                    items, total
                )
            else:
                result = _text_response("🛒 Your cart is empty! Want me to suggest something? 🍔")
        else:
            result = _text_response(
                ai_result.get('reply', ''),
                action,
                fid,
                ai_result.get('quantity', 0)
            )

        handle_cart_action(result)
        cart = session.get('cart', {})
        result['cart_count'] = sum(cart.values())
        _track_recommendation(result)

        return jsonify(result), 200

    except Exception as e:
        print(f"Chatbot AI error: {e}")
        # Fall back to the improved regex engine
        result = get_fallback_response(message, foods)
        handle_cart_action(result)
        cart = session.get('cart', {})
        result['cart_count'] = sum(cart.values())
        _track_recommendation(result)
        return jsonify(result), 200


# ---------------------------------------------------------------------------
# Cart manipulation from chatbot responses
# ---------------------------------------------------------------------------

def handle_cart_action(ai_response):
    action = ai_response.get('action')
    food_id = ai_response.get('food_id')
    if food_id is not None:
        food_id = str(food_id)
    quantity = int(ai_response.get('quantity', 1))

    if action in ('add_to_cart', 'remove_from_cart') and food_id and food_id != 'None':
        cart = session.get('cart', {})

        if action == 'add_to_cart':
            cart[food_id] = cart.get(food_id, 0) + quantity
        elif action == 'remove_from_cart':
            if food_id in cart:
                cart[food_id] -= quantity
                if cart[food_id] <= 0:
                    del cart[food_id]

        session['cart'] = cart
        session.modified = True


def _track_recommendation(result):
    """Remember the last recommended/added item for 'add it' follow-ups."""
    if result.get('action') in ('recommend',) and result.get('food_id'):
        session['chatbot_last_recommended'] = {
            'food_id': result['food_id'],
            'name': result.get('reply', ''),
        }
        session.modified = True
    elif result.get('action') == 'add_to_cart' and result.get('food_id'):
        # Clear last recommendation after it was added
        session.pop('chatbot_last_recommended', None)
        session.modified = True
