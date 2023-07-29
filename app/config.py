from app.common.config import Config as CommonConfig
from app.common.config.utils import getenv, getenv_typed


class Config(CommonConfig):
    telegram_bot_token: str
    telegram_bot_url: str
    developer_chat_id: int
    login_supported_domain: list[str]

    @staticmethod
    def load():
        super(Config, Config).load()
        Config.telegram_bot_token = getenv('TELEGRAM_BOT_TOKEN')
        Config.telegram_bot_url = getenv('TELEGRAM_BOT_URL')
        Config.developer_chat_id = getenv_typed('DEVELOPER_CHAT_ID', int)
        Config.login_supported_domain = getenv_typed('LOGIN_SUPPORTED_DOMAIN', lambda x: x.split(','))
