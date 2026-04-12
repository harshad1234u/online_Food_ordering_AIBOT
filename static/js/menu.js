document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    loadFoods();
    
    document.getElementById('search-btn').addEventListener('click', () => {
        const query = document.getElementById('search-input').value;
        const activeCat = document.querySelector('#category-list .active').dataset.cat;
        loadFoods(activeCat, query);
    });

    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if(e.key === 'Enter') {
            document.getElementById('search-btn').click();
        }
    });
});

async function loadCategories() {
    try {
        const res = await fetch('/api/menu/categories');
        const cats = await res.json();
        const list = document.getElementById('category-list');
        
        cats.forEach(c => {
            const li = document.createElement('li');
            li.innerHTML = `<a href="#" data-cat="${c}">${c}</a>`;
            list.appendChild(li);
        });

        // Add event listeners
        document.querySelectorAll('#category-list a').forEach(a => {
            a.addEventListener('click', (e) => {
                e.preventDefault();
                document.querySelectorAll('#category-list a').forEach(el => el.classList.remove('active'));
                e.target.classList.add('active');
                
                const cat = e.target.dataset.cat;
                const search = document.getElementById('search-input').value;
                loadFoods(cat, search);
            });
        });
    } catch(e) { console.error("Failed to load categories", e); }
}

async function loadFoods(category = '', search = '') {
    const grid = document.getElementById('food-grid');
    grid.innerHTML = '<div class="loader">Loading menu...</div>';
    
    let url = '/api/menu/?';
    if(category) url += `category=${encodeURIComponent(category)}&`;
    if(search) url += `search=${encodeURIComponent(search)}`;
    
    try {
        const res = await fetch(url);
        const foods = await res.json();
        
        if(foods.length === 0) {
            grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center;">No food items found.</p>';
            return;
        }
        
        grid.innerHTML = foods.map(f => `
            <div class="food-card glass">
                <img src="${f.image_url || '/static/images/default_food.png'}" onerror="this.onerror=null; this.src='/static/images/default_food.png';" alt="${f.name}" class="food-img">
                <div class="food-info">
                    <span class="food-category">${f.category}</span>
                    <h4>${f.name}</h4>
                    <p class="food-desc">${f.description}</p>
                    <div class="food-bottom">
                        <span class="food-price">₹${f.price}</span>
                        <button class="btn btn-primary btn-sm" onclick="addToCart(${f.food_id})">
                            <i class="fa-solid fa-plus"></i> Add
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch(e) {
        grid.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: red;">Error loading menu.</p>';
    }
}

async function addToCart(food_id) {
    try {
        const res = await fetch('/api/cart/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({food_id: food_id, quantity: 1})
        });
        const data = await res.json();
        if(res.ok) {
            const badge = document.querySelector('.cart-count.badge');
            badge.style.display = 'inline-block';
            badge.innerText = data.cart_count;
            // Optionally show a toast
            alert('Added to cart!');
        } else {
            alert('Error adding to cart');
        }
    } catch(e) {
        console.error(e);
    }
}
