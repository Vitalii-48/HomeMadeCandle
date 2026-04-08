# extensions.py
# Ініціалізація Flask-розширень без прив'язки до конкретного застосунку.
# Це дозволяє уникнути циклічних імпортів: розширення створюються тут,
# а підключаються до app у create_app() через .init_app(app).

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# ORM для роботи з базою даних
db = SQLAlchemy()

# Менеджер міграцій схеми БД (Alembic під капотом)
migrate = Migrate()

# Менеджер аутентифікації користувачів
login_manager = LoginManager()

# Маршрут, на який Flask-Login перенаправляє неавторизованих користувачів
login_manager.login_view = "admin.login"

# Повідомлення для неавторизованих (опціонально, але корисно для UX)
login_manager.login_message = "Будь ласка, увійдіть для доступу до цієї сторінки."
login_manager.login_message_category = "warning"

# Імпорт моделі тут — після оголошення db — щоб уникнути циклічних імпортів
from models import User  # noqa: E402


@login_manager.user_loader
def load_user(user_id):
    """
    Функція завантаження користувача для Flask-Login.

    Викликається автоматично при кожному запиті, якщо користувач авторизований.
    Повертає об'єкт User або None, якщо користувача не знайдено.

    Args:
        user_id (str): ID користувача зі збереженої сесії (завжди рядок).

    Returns:
        User | None: об'єкт користувача або None.
    """
    return db.session.get(User, int(user_id))