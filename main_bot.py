from app.bot import Bot
from app.config import Config
from app.database.migrations import apply_migrations
from app.logging import setup_app_logger


if __name__ == '__main__':
    Config.load()
    setup_app_logger('app_bot.log')
    apply_migrations()
    Bot().start()
