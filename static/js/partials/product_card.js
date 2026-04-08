// static/js/partials/product_card.js
// Весь JS для картки товару (templates/partials/product_card.html)
// URL для API (cart_add, redirect) та дані (product_id, basePrice, colors)
// передаються через data-атрибути кнопок та елементів у шаблоні

// Додавання товару до кошика
function addToCart(btn) {
  const productId   = parseInt(btn.dataset.productId);
  const cartAddUrl  = btn.dataset.cartUrl;
  const redirectUrl = btn.dataset.redirectUrl;

  const selected = document.querySelector(`input[name="color-${productId}"]:checked`);
  const colorId  = selected ? parseInt(selected.value) : null;

  fetch(cartAddUrl, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ product_id: productId, quantity: 1, color_id: colorId })
  }).then(res => {
    if (res.ok) {
      location.href = redirectUrl;
    }
  });
}

// Оновлення ціни при виборі кольору в картці.
// ВИПРАВЛЕНО: замість Jinja2 ({{ product.id }}, {{ product.price|int }})
// читаємо дані з data-атрибутів картки — JS файл не рендериться Jinja2.
document.querySelectorAll('.card-body[data-product-id]').forEach(cardBody => {
  const productId = cardBody.dataset.productId;
  const basePrice = parseInt(cardBody.dataset.basePrice);

  cardBody.querySelectorAll(`input[name="color-${productId}"]`).forEach(el => {
    el.addEventListener('change', () => {
      const colorData = JSON.parse(cardBody.dataset.colors);
      const found     = colorData.find(c => c.id == el.value);
      const modifier  = found ? (found.price_modifier || 0) : 0;
      const price     = Math.round(basePrice * (1 + modifier / 100));

      // Оновлюємо ціну лише в межах цієї картки
      cardBody.querySelector('.price-display').textContent = `Ціна: ${price} грн.`;
    });
  });
});