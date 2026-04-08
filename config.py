# config.py
# Конфігурація застосунку. Всі чутливі дані зчитуються зі змінних середовища
# (файл .env для локальної розробки, реальні env vars для продакшену).

import os
from dotenv import load_dotenv

# Завантаження змінних із файлу .env (ігнорується, якщо файл відсутній)
load_dotenv()


class Config:
    """
    Базовий клас конфігурації Flask-застосунку.

    Для різних середовищ (розробка / продакшен / тести) можна створити
    дочірні класи: DevelopmentConfig, ProductionConfig, TestingConfig.
    """

    # --- Безпека ---
    # Секретний ключ для підпису сесій та CSRF-токенів.
    # ОБОВ'ЯЗКОВО встановити у .env або середовищі деплою.
    SECRET_KEY = os.environ.get("HMC_SECRET_KEY")

    # --- База даних ---
    # URI підключення до PostgreSQL (або SQLite для локальної розробки).
    # Формат: postgresql://user:password@host:port/dbname
    SQLALCHEMY_DATABASE_URI = os.environ.get("HMC_DATABASE_URL")

    # Вимикаємо зайве відстеження змін SQLAlchemy (економить пам'ять)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Завантаження файлів ---
    # Максимальний розмір файлу, що завантажується (10 МБ)
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    # Директорія для збереження завантажених зображень
    UPLOAD_FOLDER = "static/img/uploads"

    # --- Telegram-сповіщення ---
    # Токен бота та ID чату для надсилання сповіщень про нові замовлення
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")