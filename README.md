# HomeMadeCandle — Інтернет-магазин формових свічок

Веб-додаток на Flask: публічний сайт + адмін-панель.  
Bootstrap-адаптивність, кошик у сесії, зображення у Supabase Storage, OTP-верифікація телефону, сповіщення у Telegram.

---

## Технології

- **Backend:** Python 3.12+, Flask 3, SQLAlchemy 2, Flask-Migrate (Alembic)
- **БД:** PostgreSQL (через psycopg2)
- **Зображення:** Supabase Storage + Pillow (прев'ю 200×200)
- **Аутентифікація:** Flask-Login (адмінка)
- **Доставка:** Нова Пошта API v2 (+ fake-заглушка для розробки)
- **Сповіщення:** Telegram Bot API

---

## Структура проєкту

```
├── app.py                    # Application factory (create_app)
├── config.py                 # Конфігурація зі змінних середовища
├── extensions.py             # db, migrate, login_manager
├── models.py                 # ORM-моделі (Product, Order, Composition …)
├── requirements.txt
├── Procfile                  # Gunicorn для Heroku/Render
├── .env                      # Локальні змінні (не комітити!)
├── .gitignore
│
├── blueprints/
│   ├── public/               # Головна, каталог, картка товару, FAQ
│   ├── shop/                 # Кошик, оформлення замовлення, OTP, НП
│   └── admin/                # Логін, товари, замовлення, композиції, палітра
│
├── services/
│   ├── cart.py               # Сесійний кошик
│   ├── images.py             # Supabase Storage: upload + preview
│   ├── otp.py                # OTP-верифікація телефону
│   ├── telegram.py           # Сповіщення про нові замовлення
│   └── nova_poshta/
│       ├── __init__.py       # Перемикач fake ↔ real
│       ├── fake.py           # Заглушка для локальної розробки
│       └── real.py           # Реальний API Нової Пошти
│
├── templates/                # Jinja2-шаблони (Bootstrap 5)
│   ├── base.html
│   ├── partials/             # header, footer, color_picker, faq_items, product_card
│   ├── public/               # index, catalog, product_detail, compositions, faq, privacy
│   ├── shop/                 # cart, checkout, order_success
│   └── admin/                # login, index, product_form, product_list,
│                             # composition_form, composition_list, order_list, palette
└── static/
    ├── css/
    ├── js/
    │   ├── admin/product_form.js
    │   └── public/product_detail.js
    └── img/
```

---

## Локальний запуск

### 1. Клонувати та створити середовище

```bash
git clone <repo-url>
cd HomeMadeCandle

python -m venv .venv
.venv\Scripts\activate       # Windows
# або
source .venv/bin/activate    # macOS / Linux

pip install -r requirements.txt
```

### 2. Налаштувати `.env`

Створи файл `.env` у корені проєкту:

```env
HMC_SECRET_KEY=your-secret-key-here
HMC_DATABASE_URL=postgresql://user:password@localhost:5432/homemadecandle

SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your-supabase-anon-key

TELEGRAM_BOT_TOKEN=123456:ABC-your-token
TELEGRAM_CHAT_ID=123456789

# Опціонально (для продакшен-доставки через НП)
NOVA_POSHTA_API_KEY=your-np-api-key
```

### 3. Ініціалізувати БД

```bash
flask db init          # лише перший раз — створює папку migrations/
flask db migrate -m "init"
flask db upgrade
```

### 4. Створити адміністратора

```bash
flask shell
```
```python
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

u = User(email="admin@example.com", password_hash=generate_password_hash("your-password"))
db.session.add(u)
db.session.commit()
```

### 5. Запустити

```bash
flask run
```

Сайт: http://localhost:5000  
Адмінка: http://localhost:5000/admin

---


## Основні можливості

- Каталог товарів із слайдером фото та вибором кольору
- Прев'ю-зображення 200×200 (генеруються автоматично через Pillow)
- Кошик із редагуванням кількості (без перезавантаження сторінки)
- Оформлення замовлення з OTP-верифікацією телефону
- Вибір доставки: Нова Пошта (місто + відділення) або самовивіз
- Telegram-сповіщення адміну при новому замовленні
- Адмінка: CRUD товарів, кольорів, фото, композицій, замовлень
- Глобальна палітра кольорів (копіюється на новий товар автоматично)
- Drag & drop сортування фото товарів

---

## Перехід на реальний API Нової Пошти

У `services/nova_poshta/__init__.py`:
```python
# замінити:
from .fake import search_cities, get_warehouses
# на:
from .real import search_cities, get_warehouses
```
Та додати `NOVA_POSHTA_API_KEY` у `.env`.

---

## Динамічний рік у футері

У `app.py` (`_register_jinja_globals`) додай:
```python
from datetime import datetime
app.jinja_env.globals["now"] = datetime.now
```
Тоді у `footer.html` працює `{{ now().year }}` замість захардкодженого року.

---

## Примітки

- Міграції — після кожної зміни `models.py`: `flask db migrate -m "опис"` → `flask db upgrade`
- При `joinedload` на колекції завжди використовуй `.unique().all()` (вимога SQLAlchemy 2.x)
- Не імпортуй `app` у `models.py` — лише `db` з `extensions.py` (уникнення циклічних імпортів)
- Зображення зберігаються у Supabase Storage (bucket `images_candles`)
- `.env` — ніколи не комітити у git