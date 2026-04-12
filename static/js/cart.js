document.addEventListener('DOMContentLoaded', () => {
    loadCart();

    document.getElementById('checkout-btn').addEventListener('click', async () => {
        // Redirect to payment page
        window.location.href = '/payment';
    });
});

async function loadCart() {
    try {
        const res = await fetch('/api/cart/');
        const data = await res.json();
        
        const container = document.getElementById('cart-items');
        
        if(!data.items || data.items.length === 0) {
            container.innerHTML = '<div class="empty-cart-message">Your cart is empty. <a href="/menu">Browse Menu</a></div>';
            document.getElementById('checkout-btn').disabled = true;
            return;
        }
        
        document.getElementById('checkout-btn').disabled = false;
        
        container.innerHTML = data.items.map(item => `
            <div class="cart-item glass" id="cart-item-${item.food_id}">
                <img src="${item.image_url || '/static/images/default_food.png'}" onerror="this.onerror=null; this.src='/static/images/default_food.png';" alt="${item.name}">
                <div class="cart-item-info">
                    <h4>${item.name}</h4>
                    <div class="cart-item-price">₹${item.price.toFixed(2)} / each</div>
                </div>
                <div class="qty-controls">
                    <button class="qty-btn" onclick="updateQty(${item.food_id}, ${item.quantity - 1})">-</button>
                    <span>${item.quantity}</span>
                    <button class="qty-btn" onclick="updateQty(${item.food_id}, ${item.quantity + 1})">+</button>
                </div>
                <div style="width: 80px; text-align: right; font-weight: bold;">
                    ₹${item.item_total.toFixed(2)}
                </div>
                <button class="remove-btn" onclick="removeItem(${item.food_id})"><i class="fa-solid fa-trash"></i></button>
            </div>
        `).join('');
        
        document.getElementById('cart-subtotal').innerText = '₹' + data.total.toFixed(2);
        document.getElementById('cart-total').innerText = '₹' + (data.total + 50.00).toFixed(2); // with delivery fee
        
    } catch(e) {
        console.error("Failed to load cart", e);
    }
}

async function updateQty(food_id, newQty) {
    if(newQty <= 0) {
        return removeItem(food_id);
    }
    await fetch('/api/cart/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({food_id, quantity: newQty})
    });
    loadCart();
    
    // Update global badge
    updateCartBadge();
}

async function removeItem(food_id) {
    await fetch('/api/cart/remove', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({food_id})
    });
    loadCart();
    updateCartBadge();
}

async function updateCartBadge() {
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
    } catch(e) {}
}
