// static/js/shop/cart.js
// JS для сторінки кошика (templates/shop/cart.html)
// URL для API передаються через data-атрибути #cart-config у шаблоні

document.addEventListener('DOMContentLoaded', () => {

  const config        = document.getElementById('cart-config').dataset;
  // Базові URL: у шаблоні генеруємо з index=0, тут замінюємо /0 на /
  // щоб підставляти реальний індекс позиції
  const updateBaseUrl = config.updateUrl.replace('/0', '/');
  const removeBaseUrl = config.removeUrl.replace('/0', '/');

  // ===== ОНОВЛЕННЯ КІЛЬКОСТІ ТОВАРУ =====
  document.querySelectorAll('[data-action="qty-update"]').forEach(el => {
    el.addEventListener('change', async (e) => {
      const index = e.target.dataset.index;
      const qty   = parseInt(e.target.value);
      if (qty < 1) { e.target.value = 1; return; } // захист від 0 та від'ємних

      await fetch(updateBaseUrl + index, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ quantity: qty })
      });
      location.reload();
    });
  });

  // ===== ВИДАЛЕННЯ ПОЗИЦІЇ З КОШИКА =====
  document.querySelectorAll('[data-action="remove"]').forEach(el => {
    el.addEventListener('click', async (e) => {
      // currentTarget — безпечніше за target: не залежить від дочірніх елементів кнопки
      const index = e.currentTarget.dataset.index;
      await fetch(removeBaseUrl + index, { method: 'POST' });
      location.reload();
    });
  });

});