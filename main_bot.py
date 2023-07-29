from app.bot import Bot
from app.common.database.migrations import apply_migrations
from app.config import Config


def main_bot():
    Config.load()
    Config.setup_app_logger('app_bot.log')
    apply_migrations()
    Bot().start()


def exit_bot():
    Bot().stop()


if __name__ == '__main__':
    main_bot()
