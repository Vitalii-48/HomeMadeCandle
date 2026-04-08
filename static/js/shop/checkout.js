// static/js/shop/checkout.js
// JS для сторінки оформлення замовлення (templates/shop/checkout.html)
// URL для API передаються через data-атрибути #api-urls у шаблоні

document.addEventListener('DOMContentLoaded', () => {

  // Зчитуємо всі API URL з одного прихованого div у шаблоні
  const apiUrls = document.getElementById('api-urls').dataset;

  // ─────────────────────────────────────────────
  // OTP: ВІДПРАВКА КОДУ ВЕРИФІКАЦІЇ
  // ─────────────────────────────────────────────
  document.getElementById('send-code-btn').addEventListener('click', async () => {
    const phone = document.getElementById('phone').value.trim();
    if (!phone) { alert('Введіть номер телефону'); return; }

    const res  = await fetch(apiUrls.sendUrl, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ phone })
    });
    const data = await res.json();

    if (data.ok) {
      document.getElementById('code-section').style.display = 'block';
      // ЕМУЛЯЦІЯ: в продакшні код надсилається SMS, тут показуємо у alert
      alert(`Ваш код: ${data.demo_code}`);
    } else {
      alert(data.error || 'Помилка при відправці коду');
    }
  });

  // ─────────────────────────────────────────────
  // OTP: ПЕРЕВІРКА КОДУ ВЕРИФІКАЦІЇ
  // ─────────────────────────────────────────────
  document.getElementById('verify-btn').addEventListener('click', async () => {
    const phone    = document.getElementById('phone').value.trim();
    const code     = document.getElementById('code-input').value.trim();
    const errorMsg = document.getElementById('error-msg');

    const res  = await fetch(apiUrls.checkUrl, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ phone, code })
    });
    const data = await res.json();

    if (data.ok) {
      // Верифікація успішна — показуємо підтвердження і розблоковуємо submit
      document.getElementById('verified-msg').style.display = 'block';
      errorMsg.style.display                                = 'none';
      document.getElementById('submit-btn').disabled        = false;
      document.getElementById('verify-btn').disabled        = true;
    } else {
      errorMsg.textContent   = data.error || 'Невірний код';
      errorMsg.style.display = 'block';
    }
  });

  // ─────────────────────────────────────────────
  // ПЕРЕМИКАННЯ СПОСОБУ ДОСТАВКИ
  // Показуємо/ховаємо поля Нової Пошти залежно від вибору
  // ─────────────────────────────────────────────
  document.querySelectorAll('input[name="delivery_type"]').forEach(radio => {
    radio.addEventListener('change', () => {
      document.getElementById('np-section').style.display =
        radio.value === 'nova_poshta' ? 'block' : 'none';
    });
  });

  // ─────────────────────────────────────────────
  // ПОШУК МІСТ НОВОЇ ПОШТИ (з debounce 300ms)
  // Мінімум 2 символи для запиту
  // ─────────────────────────────────────────────
  let cityTimeout;
  document.getElementById('np-city-input').addEventListener('input', function () {
    clearTimeout(cityTimeout);
    const q = this.value.trim();

    if (q.length < 2) {
      document.getElementById('city-suggestions').style.display = 'none';
      return;
    }

    cityTimeout = setTimeout(async () => {
      const res    = await fetch(`${apiUrls.citiesUrl}?q=${encodeURIComponent(q)}`);
      const cities = await res.json();
      const box    = document.getElementById('city-suggestions');
      box.innerHTML = '';

      if (cities.length === 0) { box.style.display = 'none'; return; }

      cities.forEach(city => {
        const item       = document.createElement('a');
        item.className   = 'list-group-item list-group-item-action';
        item.textContent = city.name;
        item.href        = '#';
        item.addEventListener('click', e => {
          e.preventDefault();
          // Заповнюємо видиме поле і приховані inputs для форми
          document.getElementById('np-city-input').value = city.name;
          document.getElementById('np-city-ref').value   = city.ref;
          document.getElementById('np-city-name').value  = city.name;
          box.style.display = 'none';
          loadWarehouses(city.ref);
        });
        box.appendChild(item);
      });
      box.style.display = 'block';
    }, 300);
  });

  // ─────────────────────────────────────────────
  // ЗАВАНТАЖЕННЯ ВІДДІЛЕНЬ ПІСЛЯ ВИБОРУ МІСТА
  // ─────────────────────────────────────────────
  async function loadWarehouses(cityRef) {
    const res        = await fetch(`${apiUrls.warehousesUrl}?city_ref=${cityRef}`);
    const warehouses = await res.json();
    const select     = document.getElementById('np-warehouse');
    select.innerHTML = '';
    select.disabled  = false;

    warehouses.forEach(w => {
      const opt       = document.createElement('option');
      opt.value       = w.ref;
      opt.textContent = w.name;
      select.appendChild(opt);
    });
  }

});