// static/js/admin/product_form.js
// Весь JS для сторінки створення/редагування товару (admin/product_form.html)
// URL для API передаються через data-атрибути div#admin-config у шаблоні

document.addEventListener("DOMContentLoaded", () => {

  // ===== CONFIG: читаємо URL з data-атрибутів =====
  const config       = document.getElementById('admin-config').dataset;
  const colorDelBase = config.colorDeleteUrl.replace('/0/delete', '/');
  const imageDelBase = config.imageDeleteUrl.replace('/0/delete', '/');
  const reorderUrl   = config.imagesReorderUrl;

  // ===== ПОЗНАЧЕННЯ ФОРМИ ЯК ЗМІНЕНОЇ =====
  function markDirty() {
    const saveBtn = document.getElementById("save-btn");
    if (!saveBtn) return;
    saveBtn.textContent = "Зберегти все";
    saveBtn.classList.remove("btn-primary", "btn-danger");
    saveBtn.classList.add("btn-success");
  }

  // Слухаємо зміни у формі
  const form = document.querySelector("form");
  if (form) {
    form.addEventListener("input", markDirty);
    form.addEventListener("change", markDirty);
  }

  // ===== ДОДАВАННЯ РЯДКА КОЛЬОРУ =====
  window.addColorRow = function () {
    const container = document.getElementById("color-fields");
    const index     = container.querySelectorAll('.color-row').length;
    const div       = document.createElement("div");
    div.className   = "row g-2 mb-2 align-items-center color-row";
    div.innerHTML   = `
      <input type="hidden" name="color_id[]" value="new">
      <div class="col-4">
        <input name="color_name[]" class="form-control form-control-sm" placeholder="Назва">
      </div>
      <div class="col-3">
        <input name="color_hex[]" type="color" class="form-control form-control-color w-100" value="#ffffff">
      </div>
      <div class="col-3">
        <div class="input-group input-group-sm">
          <input type="number" min="0" max="100"
                 name="color_modifier_${index}"
                 class="form-control form-control-sm" value="0">
          <span class="input-group-text">%</span>
        </div>
      </div>
      <div class="col-2">
        <button type="button" class="btn btn-sm btn-outline-secondary w-100"
                onclick="this.closest('.color-row').remove()">×</button>
      </div>`;
    container.appendChild(div);
    markDirty();
  };

  // ===== ВИДАЛЕННЯ КОЛЬОРУ АБО ФОТО ЧЕРЕЗ API =====
  window.apiDelete = async function (type, id, btn) {
    if (!confirm('Видалити цей елемент?')) return;
    const url = type === 'color'
      ? `${colorDelBase}${id}/delete`
      : `${imageDelBase}${id}/delete`;
    const res = await fetch(url, { method: 'POST' });
    if (res.ok) {
      const row = btn.closest('.color-row, .image-row');
      if (row) row.remove();
      markDirty();
    }
  };

  // ===== DRAG & DROP ЗАВАНТАЖЕННЯ ФОТО =====
  const dropZone    = document.getElementById('drop-zone');
  const fileInput   = document.getElementById('file-input');
  const newPreviews = document.getElementById('new-previews');

  if (dropZone && fileInput) {
    // Підсвічування при перетягуванні
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.style.background   = '#f0f4ff';
      dropZone.style.borderColor  = '#0d6efd';
    });
    dropZone.addEventListener('dragleave', () => {
      dropZone.style.background  = '';
      dropZone.style.borderColor = '#adb5bd';
    });
    // Скидання файлів
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.style.background  = '';
      dropZone.style.borderColor = '#adb5bd';
      const dt = new DataTransfer();
      [...e.dataTransfer.files].forEach(f => dt.items.add(f));
      fileInput.files = dt.files;
      showPreviews(fileInput.files);
    });
    // Вибір через діалог
    fileInput.addEventListener('change', () => showPreviews(fileInput.files));
  }

  // Показує прев'ю вибраних фото перед збереженням
  function showPreviews(files) {
    newPreviews.innerHTML = '';
    if (!files.length) return;
    newPreviews.classList.remove('d-none');
    [...files].forEach((file, i) => {
      const reader  = new FileReader();
      reader.onload = (e) => {
        const col       = document.createElement('div');
        col.className   = 'col-4 col-md-2';
        col.innerHTML   = `
          <div class="position-relative">
            <img src="${e.target.result}" class="img-thumbnail w-100"
                 style="height:80px;object-fit:cover;">
            ${i === 0
              ? '<span class="position-absolute top-0 start-0 m-1 badge text-bg-primary" style="font-size:9px;">Головне</span>'
              : ''}
          </div>`;
        newPreviews.appendChild(col);
      };
      reader.readAsDataURL(file);
    });
  }

  // ===== СОРТУВАННЯ ІСНУЮЧИХ ФОТО DRAG & DROP =====
  const sortable = document.getElementById('image-sortable');
  let dragItem   = null;

  if (sortable) {
    sortable.querySelectorAll('.image-row').forEach(row => {
      row.setAttribute('draggable', true);

      row.addEventListener('dragstart', () => {
        dragItem = row;
        setTimeout(() => row.style.opacity = '0.4', 0);
      });
      row.addEventListener('dragend', () => {
        dragItem.style.opacity = '1';
        dragItem = null;
        updateSortOrder();
        updateMainBadge();
      });
      row.addEventListener('dragover', (e) => {
        e.preventDefault();
        if (dragItem && dragItem !== row) {
          const rect = row.getBoundingClientRect();
          sortable.insertBefore(
            dragItem,
            e.clientX < rect.left + rect.width / 2 ? row : row.nextSibling
          );
        }
      });
    });
  }

  // Оновлює бейдж "Головне" після зміни порядку
  function updateMainBadge() {
    sortable.querySelectorAll('.image-row').forEach((row, i) => {
      const wrap  = row.querySelector('.position-relative');
      const badge = row.querySelector('.badge.text-bg-primary');
      if (i === 0 && !badge) {
        const b       = document.createElement('span');
        b.className   = 'position-absolute top-0 start-0 m-1 badge text-bg-primary';
        b.style.fontSize = '10px';
        b.textContent = 'Головне';
        wrap.appendChild(b);
      } else if (i !== 0 && badge) {
        badge.remove();
      }
    });
  }

  // Відправляє новий порядок фото на сервер
  async function updateSortOrder() {
    const ids = [...sortable.querySelectorAll('.image-row')].map(r => r.dataset.id);
    await fetch(reorderUrl, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ order: ids })
    });
  }

}); // DOMContentLoaded