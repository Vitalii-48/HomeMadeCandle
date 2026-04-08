  // static/js/public/product_detail.js

document.addEventListener('DOMContentLoaded', () => {

  const productData = document.getElementById('product-data');
  const productId   = productData.dataset.id;  // рядок, не parseInt — для селектора
  const priceBase   = parseInt(productData.dataset.price);
  const cartUrl     = productData.dataset.cartUrl;
  const cartAddUrl  = productData.dataset.cartAddUrl;

  const qty         = document.getElementById('qty');
  const priceEl     = document.getElementById('price-display');
  // Використовуємо productId з data-атрибута замість {{ product.id }}
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
    if (res.ok) window.location.href = cartUrl;
  };

});
