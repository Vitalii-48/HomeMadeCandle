# services/images.py
import os, uuid
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app
from io import BytesIO
from supabase import create_client

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}
BUCKET = "images_candles"

def get_supabase():
    return create_client(
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_KEY")
    )

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file_storage):
    filename = file_storage.filename
    if not allowed_file(filename):
        raise ValueError("Недопустиме розширення файлу")

    ext = filename.rsplit(".", 1)[1].lower()
    unique = f"{uuid.uuid4().hex}.{ext}"

    # Оригінал
    file_bytes = file_storage.read()
    supabase = get_supabase()
    supabase.storage.from_(BUCKET).upload(unique, file_bytes)

    # Прев'ю 200x200
    img = Image.open(BytesIO(file_bytes))
    if ext in ("jpg", "jpeg", "webp"):
        img = img.convert("RGB")
    img.thumbnail((200, 200))
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    preview_name = f"preview_{unique}"
    supabase.storage.from_(BUCKET).upload(preview_name, buf.read())

    return unique, preview_name

def get_image_url(filename):
    supabase = get_supabase()
    return supabase.storage.from_(BUCKET).get_public_url(filename)

def delete_image(filename):
    if not filename:
        return
    supabase = get_supabase()
    supabase.storage.from_(BUCKET).remove([filename])

def delete_images(filenames):
    filenames = [f for f in filenames if f]  # прибираємо None
    if not filenames:
        return
    supabase = get_supabase()
    supabase.storage.from_(BUCKET).remove(filenames)