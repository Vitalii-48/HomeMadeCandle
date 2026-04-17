// static/js/partials/product_card.js
// Весь JS для картки товару (templates/partials/product_card.html)
// URL для API (cart_add, redirect) та дані (product_id, basePrice, colors)
// передаються через data-атрибути кнопок та елементів у шаблоні


// Оновлення всіх бейджів кошика на сторінці
function updateCartBadges(count) {
  const badge = document.getElementById("cart-count-badge");
  if (badge) {
    badge.textContent = count;
  }
}

// Додавання товару до кошика
function addToCart(btn) {
  const productId  = parseInt(btn.dataset.productId);
  const cartAddUrl = btn.dataset.cartUrl;

  const selected = document.querySelector(`input[name="color-${productId}"]:checked`);
  const colorId  = selected ? parseInt(selected.value) : null;

  fetch(cartAddUrl, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ product_id: productId, quantity: 1, color_id: colorId })
  })
  .then(res => res.json())
  .then(data => {
    if (data.ok) {
      // Оновлюємо всі бейджі лічильника
      if (data.cart_count !== undefined) {
        updateCartBadges(data.cart_count);
      }

      // Видаляємо старі toast
      document.querySelectorAll(".toast-cart").forEach(t => t.remove());

      // Toast повідомлення
      const toast = document.createElement("div");
      toast.className = "toast-cart toast align-items-center text-bg-success border-0 show position-fixed bottom-0 end-0 m-3";
      toast.style.zIndex = "9999";
      toast.innerHTML = `
        <div class="d-flex">
          <div class="toast-body">Товар додано в кошик 🛒</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto"></button>
        </div>
      `;
      document.body.appendChild(toast);
      toast.querySelector(".btn-close").onclick = () => toast.remove();
      setTimeout(() => toast.remove(), 3000);
    }
  })
  .catch(err => console.error("Помилка додавання до кошика:", err));
}


// Оновлення ціни при виборі кольору в картці
document.querySelectorAll('.card-body[data-product-id]').forEach(cardBody => {
  const productId = cardBody.dataset.productId;
  const basePrice = parseInt(cardBody.dataset.basePrice);

  cardBody.querySelectorAll(`input[name="color-${productId}"]`).forEach(el => {
    el.addEventListener('change', () => {
      const colorData = JSON.parse(cardBody.dataset.colors);
      const found     = colorData.find(c => c.id == el.value);
      const modifier  = found ? (found.price_modifier || 0) : 0;
      const price     = Math.round(basePrice * (1 + modifier / 100));
      cardBody.querySelector('.price-display').textContent = `Ціна: ${price} грн.`;
    });
  });
});
