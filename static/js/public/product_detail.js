// static/js/public/product_detail.js

// Оновлення всіх бейджів кошика на сторінці
function updateCartBadges(count) {
  const badge = document.getElementById("cart-count-badge");
  if (badge) {
    badge.textContent = count;
  }
}

document.addEventListener('DOMContentLoaded', () => {

  const productData = document.getElementById('product-data');
  const productId   = productData.dataset.id;
  const priceBase   = parseInt(productData.dataset.price);
  const cartAddUrl  = productData.dataset.cartAddUrl;

  const qty      = document.getElementById('qty');
  const priceEl  = document.getElementById('price-display');
  const colorInputs = document.querySelectorAll(`input[name="color-${productId}"]`);

  // Керування кількістю
  document.getElementById('qty-minus').onclick = () =>
    qty.value = Math.max(1, parseInt(qty.value) - 1);
  document.getElementById('qty-plus').onclick  = () =>
    qty.value = parseInt(qty.value) + 1;

  // Оновлення ціни при зміні кольору
  function updatePrice() {
    const selected = document.querySelector(`input[name="color-${productId}"]:checked`);
    if (!selected) return;
    const colors   = JSON.parse(productData.dataset.colors);
    const found    = colors.find(c => c.id == selected.value);
    const modifier = found ? (found.price_modifier || 0) : 0;
    const price    = Math.round(priceBase * (1 + modifier / 100));
    priceEl.textContent = `Ціна: ${price} грн.`;
  }

  colorInputs.forEach(el => el.addEventListener('change', updatePrice));
  updatePrice();

  // Додавання до кошика
  document.getElementById('add-to-cart').onclick = async () => {
    const selected = document.querySelector(`input[name="color-${productId}"]:checked`);
    const colorId  = selected ? parseInt(selected.value) : null;

    const res = await fetch(cartAddUrl, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({
        product_id: parseInt(productId),
        color_id:   colorId,
        quantity:   parseInt(qty.value)
      })
    });
    const data = await res.json();

    if (data.ok) {
      // Оновлюємо всі бейджі лічильника (мобільний і десктопний)
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
  };

});
