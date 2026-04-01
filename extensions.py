# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "admin.login"

from models import User

# Завантаження користувача для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))