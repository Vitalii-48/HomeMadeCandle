import sys
from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from extensions import db
from models import Color, Composition, Product


@pytest.fixture
def app():
    class TestingConfig:
        TESTING = True
        SECRET_KEY = "test-secret-key"
        SQLALCHEMY_DATABASE_URI = "sqlite://"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
        TELEGRAM_BOT_TOKEN = None
        TELEGRAM_CHAT_ID = None

    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_data(app):
    with app.app_context():
        product = Product(
            sku="1001",
            name="Тестова свічка",
            description="Проста тестова свічка",
            price=250,
            is_active=True,
        )
        db.session.add(product)
        db.session.flush()

        color = Color(
            product_id=product.id,
            color_name="Білий",
            color_hex="#FFFFFF",
            price_modifier=10,
            is_default=True,
        )
        composition = Composition(
            title="Тестова композиція",
            description="Композиція для тестів",
            price=700,
            is_active=True,
        )

        db.session.add_all([color, composition])
        db.session.commit()

        return {
            "product_id": product.id,
            "color_id": color.id,
            "composition_id": composition.id,
        }
