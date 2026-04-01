# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("HMC_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "HMC_DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB upload limit
    UPLOAD_FOLDER = "static/img/uploads"