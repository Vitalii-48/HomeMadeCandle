# services/images.py
# Завантаження та видалення зображень у Supabase Storage.
# Автоматично генерує прев'ю 200×200 для кожного фото.

import os
import uuid
from io import BytesIO

from PIL import Image
from flask import current_app
from supabase import create_client

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
PREVIEW_SIZE = (200, 200)   # розмір прев'ю в пікселях
BUCKET = "images_candles"   # назва bucket у Supabase Storage


def _get_supabase():
    """
    Створює та повертає клієнт Supabase.
    Викликається при кожній операції — клієнт легкий, кешування не потрібне.
    Змінні середовища читаються з .env через config.py.
    """
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL або SUPABASE_KEY не задані у .env")
    return create_client(url, key)


def allowed_file(filename: str) -> bool:
    """Перевіряє, чи є розширення файлу допустимим."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file_storage) -> tuple[str, str]:
    """
    Зберігає зображення та його прев'ю у Supabase Storage.

    Кроки:
    1. Перевірка розширення.
    2. Генерація унікального імені файлу (uuid).
    3. Завантаження оригіналу.
    4. Генерація прев'ю 200×200 через Pillow і завантаження.

    Args:
        file_storage: об'єкт FileStorage з Flask request.files.

    Returns:
        (unique_filename, preview_filename): імена файлів у Supabase.

    Raises:
        ValueError: якщо розширення файлу недопустиме.
        RuntimeError: якщо SUPABASE_URL/KEY не задані.
    """
    if not allowed_file(file_storage.filename):
        raise ValueError(f"Недопустиме розширення файлу: {file_storage.filename}")

    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    preview_name = f"preview_{unique_name}"

    file_bytes = file_storage.read()
    supabase = _get_supabase()

    # Завантажуємо оригінал
    supabase.storage.from_(BUCKET).upload(unique_name, file_bytes)

    # Генеруємо та завантажуємо прев'ю
    img = Image.open(BytesIO(file_bytes))
    if ext in ("jpg", "jpeg", "webp"):
        img = img.convert("RGB")  # прибираємо прозорість для JPEG-сумісності
    img.thumbnail(PREVIEW_SIZE)
    buf = BytesIO()
    img.save(buf, format="PNG")
    supabase.storage.from_(BUCKET).upload(preview_name, buf.getvalue())

    return unique_name, preview_name


def get_image_url(filename: str) -> str | None:
    """
    Повертає публічний URL зображення з Supabase Storage.
    Використовується у Jinja2-шаблонах як глобальна функція get_image_url().

    Returns:
        str: публічний URL або None якщо filename порожній.
    """
    if not filename:
        return None
    return _get_supabase().storage.from_(BUCKET).get_public_url(filename)


def delete_images(filenames: list[str]) -> None:
    """
    Видаляє список файлів із Supabase Storage.
    None та порожні рядки у списку ігноруються.
    Якщо список порожній — нічого не робить.

    Args:
        filenames: список імен файлів для видалення.
    """
    filenames = [f for f in filenames if f]
    if not filenames:
        return
    _get_supabase().storage.from_(BUCKET).remove(filenames)