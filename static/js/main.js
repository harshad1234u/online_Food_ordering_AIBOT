document.addEventListener('DOMContentLoaded', () => {
    checkAuthStatus();
    updateCartCount();
    initChatbot();
});

// Auth Status check
async function checkAuthStatus() {
    try {
        const res = await fetch('/api/me');
        const authLinks = document.getElementById('auth-links');

        if(res.ok) {
            const user = await res.json();
            let html = `
                <a href="/orders"><i class="fa-solid fa-list"></i> Orders</a>
                <a href="#" id="logout-btn"><i class="fa-solid fa-sign-out-alt"></i> Logout</a>
            `;
            if (user.is_admin) {
                html = `<a href="/admin"><i class="fa-solid fa-shield"></i> Admin</a> ` + html;
            }
            authLinks.innerHTML = html;

            document.getElementById('logout-btn').addEventListener('click', async (e) => {
                e.preventDefault();
                await fetch('/api/logout', { method: 'POST' });
                window.location.href = '/';
            });
        } else {
            authLinks.innerHTML = `<a href="/login" class="btn btn-primary" style="padding: 8px 15px;">Login</a>`;
        }
    } catch(e) {
        console.error("Auth check failed");
    }
}

// Global Cart count updating
async function updateCartCount() {
    try {
        const res = await fetch('/api/cart/');
        const data = await res.json();
        const count = data.items.reduce((acc, item) => acc + item.quantity, 0);

        const badge = document.querySelector('.cart-count.badge');
        if(count > 0) {
            badge.style.display = 'inline-block';
            badge.innerText = count;
        } else {
            badge.style.display = 'none';
        }
    } catch(e) { console.error("Cart update failed"); }
}

// Update Live Cart count
function setLiveCartCount(count) {
    const badge = document.querySelector('.cart-count.badge');
    if(count > 0) {
        badge.style.display = 'inline-block';
        badge.innerText = count;
    } else {
        badge.style.display = 'none';
        badge.innerText = 0;
    }
}

// Escape HTML to prevent XSS from chat messages
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// --- Chatbot: Add to cart via API from card button ---
async function chatbotAddToCart(foodId, foodName) {
    try {
        const res = await fetch('/api/cart/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ food_id: foodId, quantity: 1 })
        });
        const data = await res.json();
        if (data.cart_count !== undefined) {
            setLiveCartCount(data.cart_count);
        }

        // Show a quick confirmation in the chatbot
        const messages = document.getElementById('chatbot-messages');
        if (messages) {
            const confirmDiv = document.createElement('div');
            confirmDiv.className = 'message bot-message chat-animate-in';
            confirmDiv.textContent = `✅ ${foodName} added to cart!`;
            messages.appendChild(confirmDiv);
            messages.scrollTop = messages.scrollHeight;
        }

        // Reload cart page if on it
        if (window.location.pathname === '/cart' && typeof loadCart === 'function') {
            loadCart();
        }
    } catch(e) {
        console.error("Add to cart error:", e);
    }
}

// --- Chatbot: Render a food card list ---
function renderFoodCards(data) {
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-food-cards';

    data.forEach((item, idx) => {
        const card = document.createElement('div');
        card.className = 'chat-food-card chat-animate-in';
        card.style.animationDelay = `${idx * 0.08}s`;

        const img = item.image || '/static/images/default_food.png';
        const price = typeof item.price === 'number' ? item.price.toFixed(0) : item.price;

        card.innerHTML = `
            <div class="chat-card-img">
                <img src="${escapeHtml(img)}" alt="${escapeHtml(item.name)}" 
                     onerror="this.src='/static/images/default_food.png'">
            </div>
            <div class="chat-card-info">
                <span class="chat-card-name">${escapeHtml(item.name)}</span>
                <span class="chat-card-price">₹${escapeHtml(String(price))}</span>
            </div>
            <button class="chat-card-add" title="Add to cart" 
                    onclick="chatbotAddToCart(${item.food_id}, '${escapeHtml(item.name).replace(/'/g, "\\'")}')">
                <i class="fa-solid fa-plus"></i>
            </button>
        `;
        wrapper.appendChild(card);
    });

    return wrapper;
}

// --- Chatbot: Render a cart summary ---
function renderCartSummary(data, total) {
    const wrapper = document.createElement('div');
    wrapper.className = 'chat-cart-summary chat-animate-in';

    if (!data || data.length === 0) {
        wrapper.innerHTML = '<div class="chat-cart-empty">Your cart is empty 🛒</div>';
        return wrapper;
    }

    let html = '<div class="chat-cart-items">';
    data.forEach(item => {
        const price = typeof item.price === 'number' ? item.price.toFixed(0) : item.price;
        const itemTotal = typeof item.item_total === 'number' ? item.item_total.toFixed(0) : item.item_total;
        html += `
            <div class="chat-cart-item">
                <img src="${escapeHtml(item.image || '/static/images/default_food.png')}" 
                     alt="${escapeHtml(item.name)}"
                     onerror="this.src='/static/images/default_food.png'">
                <div class="chat-cart-item-info">
                    <span class="chat-cart-item-name">${escapeHtml(item.name)}</span>
                    <span class="chat-cart-item-qty">${item.quantity}x ₹${escapeHtml(String(price))}</span>
                </div>
                <span class="chat-cart-item-total">₹${escapeHtml(String(itemTotal))}</span>
            </div>
        `;
    });
    html += '</div>';

    const totalFormatted = typeof total === 'number' ? total.toFixed(0) : total;
    html += `
        <div class="chat-cart-total">
            <span>Total</span>
            <span class="chat-cart-total-price">₹${escapeHtml(String(totalFormatted))}</span>
        </div>
        <button class="chat-cart-checkout" onclick="window.location.href='/payment'">
            Proceed to Checkout <i class="fa-solid fa-arrow-right"></i>
        </button>
    `;

    wrapper.innerHTML = html;
    return wrapper;
}


// Chatbot UI and Logic
function initChatbot() {
    const toggle = document.getElementById('chatbot-toggle');
    const panel = document.getElementById('chatbot-panel');
    const close = document.getElementById('chatbot-close');
    const sendBtn = document.getElementById('chatbot-send');
    const input = document.getElementById('chatbot-input-field');
    const messages = document.getElementById('chatbot-messages');

    if(!toggle) return;

    // Quick suggestion chips
    const chipContainer = document.createElement('div');
    chipContainer.className = 'chat-suggestion-chips';
    chipContainer.innerHTML = `
        <button class="chat-chip" data-msg="suggest something spicy 🔥">🔥 Spicy</button>
        <button class="chat-chip" data-msg="show me veg options">🥗 Veg</button>
        <button class="chat-chip" data-msg="cheap food">💰 Budget</button>
        <button class="chat-chip" data-msg="show my cart">🛒 Cart</button>
        <button class="chat-chip" data-msg="show menu">📋 Menu</button>
    `;

    // Insert chips after the welcome message
    messages.appendChild(chipContainer);

    // Conversation history for AI context
    const conversationHistory = [];

    toggle.addEventListener('click', () => {
        panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
        if(panel.style.display === 'flex') input.focus();
    });

    close.addEventListener('click', () => {
        panel.style.display = 'none';
    });

    const sendMessage = async (overrideText) => {
        const text = (overrideText || input.value).trim();
        if(!text) return;

        // Add user message to UI
        const userDiv = document.createElement('div');
        userDiv.className = 'message user-message chat-animate-in';
        userDiv.textContent = text;
        messages.appendChild(userDiv);
        input.value = '';
        messages.scrollTop = messages.scrollHeight;

        // Track in conversation history
        conversationHistory.push({ role: 'user', content: text });

        // Add loading indicator
        const loader = document.createElement('div');
        loader.className = 'message bot-message';
        loader.innerHTML = '<div class="chat-typing"><span></span><span></span><span></span></div>';
        messages.appendChild(loader);
        messages.scrollTop = messages.scrollHeight;

        try {
            const res = await fetch('/api/chatbot/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    message: text,
                    history: conversationHistory.slice(-6)
                })
            });
            const data = await res.json();

            // Remove loader
            loader.remove();

            // Add bot reply text
            const botDiv = document.createElement('div');
            botDiv.className = 'message bot-message chat-animate-in';
            botDiv.textContent = data.reply;
            messages.appendChild(botDiv);

            // Render structured data based on response type
            if (data.type === 'list' && data.data && data.data.length > 0) {
                const cards = renderFoodCards(data.data);
                messages.appendChild(cards);
            } else if (data.type === 'cart' && data.data) {
                const cartEl = renderCartSummary(data.data, data.cart_total);
                messages.appendChild(cartEl);
            } else if (data.type === 'added' && data.data && data.data.length > 0) {
                // Show a small confirmation card for the added item
                const item = data.data[0];
                const addedDiv = document.createElement('div');
                addedDiv.className = 'chat-added-confirm chat-animate-in';
                addedDiv.innerHTML = `
                    <img src="${escapeHtml(item.image || '/static/images/default_food.png')}" 
                         alt="${escapeHtml(item.name)}"
                         onerror="this.src='/static/images/default_food.png'">
                    <div>
                        <strong>${escapeHtml(item.name)}</strong>
                        <span>₹${typeof item.price === 'number' ? item.price.toFixed(0) : item.price}</span>
                    </div>
                    <i class="fa-solid fa-circle-check" style="color: #2ed573; font-size: 1.2rem;"></i>
                `;
                messages.appendChild(addedDiv);
            }

            // Track bot reply in history
            conversationHistory.push({ role: 'assistant', content: data.reply });

            // Handle backend session cart modifications
            if(data.cart_count !== undefined) {
                setLiveCartCount(data.cart_count);
                // Reload cart view if on cart page
                if(window.location.pathname === '/cart' && typeof loadCart === 'function') {
                    loadCart();
                }
            }

            // Handle navigation intents (with short delay so user can read the reply)
            if (data.action === 'show_menu') {
                setTimeout(() => { window.location.href = '/menu'; }, 1200);
            } else if (data.action === 'place_order') {
                setTimeout(() => { window.location.href = '/payment'; }, 1200);
            }
            // NOTE: show_cart now renders in-chat, no navigation needed

            messages.scrollTop = messages.scrollHeight;
        } catch(e) {
            console.error(e);
            loader.remove();
            const errDiv = document.createElement('div');
            errDiv.className = 'message bot-message chat-animate-in';
            errDiv.textContent = "😅 Sorry, I'm having trouble connecting. Please try again!";
            messages.appendChild(errDiv);
        }
    };

    sendBtn.addEventListener('click', () => sendMessage());
    input.addEventListener('keypress', (e) => {
        if(e.key === 'Enter') sendMessage();
    });

    // Handle chip clicks
    chipContainer.addEventListener('click', (e) => {
        const chip = e.target.closest('.chat-chip');
        if (chip) {
            sendMessage(chip.dataset.msg);
        }
    });
}
