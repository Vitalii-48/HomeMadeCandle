// Додавання композиції до кошика через API
  function addComposition(cartUrl, id) {
    fetch(cartUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ composition_id: id, quantity: 1 })
    })
    .then(res => res.json())
    .then(data => {
      if (data.ok) {
        // Оновлюємо бейдж кошика
        const badge = document.getElementById("cart-count-badge");
        if (badge && data.cart_count !== undefined) {
          badge.textContent = data.cart_count;
        }

        // Видаляємо старі toast
        document.querySelectorAll(".toast").forEach(t => t.remove());

        // Створюємо toast
        const toast = document.createElement("div");
        toast.className = "toast align-items-center text-bg-success border-0 show position-fixed bottom-0 end-0 m-3";
        toast.innerHTML = `
          <div class="d-flex">
            <div class="toast-body">
              Композицію додано в кошик 🛒
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto"></button>
          </div>
        `;
        document.body.appendChild(toast);

        // Закриття toast кнопкою
        toast.querySelector(".btn-close").onclick = () => toast.remove();

        // Автоматичне закриття через 3 секунди
        setTimeout(() => toast.remove(), 3000);
      }
    })
    .catch(err => console.error("Помилка при додаванні:", err));
  }