# README.md

## Опис
Інтернет-магазин формових свічок: сайт + адмінка на Flask. Адаптивний Bootstrap, кошик у сесії, локальне завантаження фото, кольори з модифікатором ціни (+10% для небілого).

## Запуск локально
1. Створити і активувати середовище:
   - python -m venv .venv
   - .venv\Scripts\activate (Windows) або source .venv/bin/activate (macOS/Linux)
2. Встановити залежності:
   - pip install -r requirements.txt
3. Налаштувати .env:
   - створи в кореневому каталозі файл .env
   - скопіюй .env.example у .env і задай SECRET_KEY, DATABASE_URL за потреби
4. Ініціалізувати БД і міграції:
   - flask db init
   - flask db migrate -m "init"
   - flask db upgrade
5. Створити адмін-користувача (у Flask shell):
   - flask shell
   - from extensions import db
   - from models import User
   - u = User(email="admin@example.com", password_hash=generate_password_hash("123456"))
   - db.session.add(u); db.session.commit()
6. Запустити:
   - flask run

## Структура
- app.py (app factory)
- extensions.py (db, migrate, login_manager)
- models.py (Product, Color, ProductImage, Order, OrderItem, User, Composition)
- services/cart.py (сесійний кошик)
- services/images.py (Pillow: upload + preview 200x200)
- blueprints/public|shop|admin (маршрути й шаблони)
- templates (Bootstrap, адаптивність)
- static (css, js, img/uploads)

## Функції
- Каталог, картка товару з слайдером фото
- Вибір кольору
- Кошик з редагуванням кількості
- Оформлення замовлення (без email, з телефоном і методом зв’язку)
- Адмінка: логін, товари ( кольори, фото ), замовлення
- Композиції як контент (CRUD в адмінці)

## Авторство
Проект створений за допомогою штучного інтелекту (Microsoft Copilot).

## Примітки
- Міграції створюються автоматично командою `flask db migrate` після змін у models.py.
- Щоб уникнути циклічних імпортів — не імпортуй app у models; імпортуй лише `db` з extensions.py.
- За потреби додай валідацію телефонів та адрес у checkout.
