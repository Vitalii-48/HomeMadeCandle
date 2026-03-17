# main.py
import os
from flask import Flask
from config import Config
from dotenv import load_dotenv
from extensions import db, migrate, login_manager
from blueprints.public import bp as public_bp
from blueprints.shop import bp as shop_bp
from blueprints.admin import bp as admin_bp

load_dotenv()

def create_app():
    # 1. Створення Flask-застосунку
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # 2. Завантаження конфігурації
    app.config.from_object(Config)

    # 3. Ініціалізація розширень
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # 4. Реєстрація Blueprints (модульна архітектура)
    app.register_blueprint(public_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(admin_bp)

    # 5. Health-check endpoint (перевірка стану сервера)
    @app.route("/health")
    def health():
        return "OK", 200

    return app
# Запуск застосунку
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)