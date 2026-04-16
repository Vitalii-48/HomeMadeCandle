# HomeMadeCandle — Online Candle Shop

A Flask web application: public storefront + admin panel.
Bootstrap-responsive design, session-based cart, images stored in Supabase Storage, phone OTP verification, and Telegram notifications.

---

## Tech Stack

- **Backend:** Python 3.12+, Flask 3, SQLAlchemy 2, Flask-Migrate (Alembic)
- **Database:** PostgreSQL (via psycopg2)
- **Images:** Supabase Storage + Pillow (200×200 previews)
- **Authentication:** Flask-Login (admin panel)
- **Delivery:** Nova Poshta API v2 (+ fake stub for development)
- **Notifications:** Telegram Bot API

---

## Project Structure

```
├── app.py                    # Application factory (create_app)
├── config.py                 # Configuration from environment variables
├── extensions.py             # db, migrate, login_manager
├── models.py                 # ORM models (Product, Order, Composition …)
├── requirements.txt
├── Procfile                  # Gunicorn for Heroku/Render
├── .env                      # Local variables (do not commit!)
├── .gitignore
│
├── blueprints/
│   ├── public/               # Home, catalog, product detail, FAQ
│   ├── shop/                 # Cart, checkout, OTP, Nova Poshta
│   └── admin/                # Login, products, orders, compositions, palette
│
├── services/
│   ├── cart.py               # Session-based cart
│   ├── images.py             # Supabase Storage: upload + preview
│   ├── otp.py                # Phone OTP verification
│   ├── telegram.py           # New order notifications
│   └── nova_poshta/
│       ├── init.py           # fake ↔ real switcher
│       ├── fake.py           # Stub for local development
│       └── real.py           # Real Nova Poshta API
│
├── templates/                # Jinja2 templates (Bootstrap 5)
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

## Local Setup

### 1. Clone and create environment

```bash
git clone <repo-url>
cd HomeMadeCandle

python -m venv .venv
.venv\Scripts\activate       # Windows
# or
source .venv/bin/activate    # macOS / Linux

pip install -r requirements.txt
```

### 2. Configure `.env`

Create a `.env` file in the project root:

```env
HMC_SECRET_KEY=your-secret-key-here
HMC_DATABASE_URL=postgresql://user:password@localhost:5432/homemadecandle

SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your-supabase-anon-key

TELEGRAM_BOT_TOKEN=123456:ABC-your-token
TELEGRAM_CHAT_ID=123456789

# Optional (for production delivery via Nova Poshta)
NOVA_POSHTA_API_KEY=your-np-api-key
```

### 3. Initialize the database

```bash
flask db init          # first time only — creates migrations/ folder
flask db migrate -m "init"
flask db upgrade
```

### 4. Create an admin user

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

### 5. Run

```bash
flask run
```

Site: http://localhost:5000  
Admin panel: http://localhost:5000/admin

---

## Features

- Product catalog with photo slider and color selection
- Auto-generated 200×200 image previews via Pillow
- Cart with quantity editing (no page reload)
- Checkout with phone OTP verification
- Delivery options: Nova Poshta (city + branch) or pickup
- Telegram notification to admin on new order
- Admin panel: full CRUD for products, colors, photos, compositions, orders
- Global color palette (automatically copied to new products)
- Drag & drop photo sorting for products

---

## Switching to Real Nova Poshta API

In `services/nova_poshta/__init__.py`:
```python
# replace:
from .fake import search_cities, get_warehouses
# with:
from .real import search_cities, get_warehouses
```
And add `NOVA_POSHTA_API_KEY` to your `.env`.

---

## Dynamic Year in Footer

In `app.py` (`_register_jinja_globals`) add:
```python
from datetime import datetime
app.jinja_env.globals["now"] = datetime.now
```
Then in `footer.html` use `{{ now().year }}` instead of a hardcoded year.

---

## Notes

- Run migrations after every `models.py` change: `flask db migrate -m "description"` → `flask db upgrade`
- When using `joinedload` on collections, always call `.unique().all()` (SQLAlchemy 2.x requirement)
- Never import `app` in `models.py` — only import `db` from `extensions.py` (avoids circular imports)
- Images are stored in Supabase Storage (bucket `images_candles`)
- Never commit `.env` to git
