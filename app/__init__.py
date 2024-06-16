# __init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from .routes import main  # Импортируем Blueprint

    app.register_blueprint(main)  # Регистрируем Blueprint в приложении Flask

    with app.app_context():
        from . import routes, models  # Импортируем routes и models для инициализации базы данных
        db.create_all()  # Создаем все таблицы в базе данных

    return app

