# app.py
# Точка входу Flask-застосунку. Використовує фабричний патерн create_app()
# для гнучкої конфігурації та спрощення тестування.

from flask import Flask
from config import Config
from datetime import datetime
from extensions import db, migrate, login_manager
from blueprints.public import bp as public_bp
from blueprints.shop import bp as shop_bp
from blueprints.admin import bp as admin_bp
from services.images import get_image_url


def create_app(config_class=Config):
    """
    Фабрична функція для створення Flask-застосунку.

    Патерн Application Factory дозволяє:
    - створювати кілька екземплярів застосунку (наприклад, для тестів);
    - легко підміняти конфігурацію (Config / TestingConfig / ProductionConfig).

    Args:
        config_class: клас конфігурації (за замовчуванням Config).

    Returns:
        app (Flask): сконфігурований екземпляр Flask-застосунку.
    """
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)

    _register_extensions(app)
    _register_blueprints(app)
    _register_jinja_globals(app)
    _register_routes(app)

    return app


def _register_extensions(app):
    """Ініціалізація Flask-розширень (db, migrate, login_manager)."""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)


def _register_blueprints(app):
    """Реєстрація Blueprint-модулів (публічна частина, магазин, адмінка)."""
    app.register_blueprint(public_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(admin_bp)


def _register_jinja_globals(app):
    """Реєстрація глобальних функцій/змінних, доступних у всіх Jinja2-шаблонах."""
    app.jinja_env.globals["get_image_url"] = get_image_url
    app.jinja_env.globals["now"] = datetime.now

def _register_routes(app):
    """Реєстрація службових маршрутів застосунку."""

    @app.route("/health")
    def health():
        """
        Health-check endpoint.
        Використовується балансувальником навантаження або моніторингом
        для перевірки доступності сервера.
        """
        return "OK", 200


if __name__ == "__main__":
    # Локальний запуск для розробки. У продакшені використовується Gunicorn.
    app = create_app()
    app.run(debug=True)