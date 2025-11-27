import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set. Application must run via Docker with PostgreSQL.")

    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    API_TOKEN = os.environ.get("API_TOKEN", "super-secret-api-token")

    # если 1 — разрешаем много раз проходить опросы с одного IP (для тестов)
    ALLOW_MULTIPLE_RESPONSES = os.environ.get("ALLOW_MULTIPLE_RESPONSES", "0") == "1"
