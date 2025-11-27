from flask import Flask
from config import Config
from extensions import db, migrate, limiter
from models import Admin
from sqlalchemy.exc import ProgrammingError, OperationalError


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    from app.views.admin import admin_bp
    from app.views.public import public_bp
    from app.views.api import api_bp

    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(public_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # ---- создание / обновление админа ----
    with app.app_context():
        try:
            admin = Admin.query.filter_by(username="admin").first()
            if admin is None:
                admin = Admin(username="admin")
                admin.set_password("admin")
                db.session.add(admin)
            else:
                admin.set_password("admin")  # обновим пароль на 'admin'
            db.session.commit()
        except (ProgrammingError, OperationalError):
            # Таблиц ещё нет (fresh DB, до миграций) – просто игнорируем
            db.session.rollback()
    # --------------------------------------

    return app
