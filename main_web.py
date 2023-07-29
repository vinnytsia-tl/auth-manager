from app.common.database.migrations import apply_migrations
from app.config import Config
from app.web import Web


def main_web():
    Config.load()
    Config.setup_app_logger('app_web.log')
    apply_migrations()
    Web.start()


def exit_web():
    Web.stop()


if __name__ == '__main__':
    main_web()
