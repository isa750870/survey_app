import os
import sys
import pytest

# --- Делаем так, чтобы можно было писать `import models`, `import extensions` ---

# Абсолютный путь к корню проекта (директория на уровень выше /tests)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Теперь эти импорты работают так же, как в основном коде
from extensions import db
from wsgi import app as flask_app


@pytest.fixture(scope="session")
def app():
    """
    Тестовый экземпляр приложения, подключённый к PostgreSQL.
    DATABASE_URL приходит из переменных окружения (docker-compose).
    """
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        ALLOW_MULTIPLE_RESPONSES=True,  # чтобы спокойно многократно проходить опросы
    )

    with flask_app.app_context():
        # создаём таблицы по моделям (схема одна на всю сессию тестов)
        db.create_all()
        yield flask_app
        db.session.rollback()
        meta = db.metadata
        for table in reversed(meta.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()



@pytest.fixture(scope="session")
def _db(app):
    """
    Фикстура для pytest, которую могут использовать другие фикстуры.
    Называется _db, чтобы не конфликтовать с extensions.db.
    """
    return db


@pytest.fixture(autouse=True)
def clean_db(app):
    """
    Очищаем все таблицы перед каждым тестом.
    Схема (структура таблиц) сохраняется, чистятся только данные.
    """
    yield

    db.session.rollback()
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()


@pytest.fixture
def client(app):
    """HTTP-клиент Flask."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Удобная ссылка на сессию БД."""
    return db.session
