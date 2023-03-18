from app.config import Config
from app.database.migrations import apply_migrations
from app.logging import setup_app_logger
from app.web import Web


def main_web():
    Config.load()
    setup_app_logger('app_web.log')
    apply_migrations()
    Web.start()


if __name__ == '__main__':
    main_web()
