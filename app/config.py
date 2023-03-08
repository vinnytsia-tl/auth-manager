import logging
import os
from typing import List

import dotenv
import jinja2

from app.database import Database
from app.system.ldap import LDAP, LDAPConfig


class Config:
    production: bool = None
    telegram_bot_token: str = None
    telegram_bot_url: str = None
    developer_chat_id: int = None
    log_directory: str = None
    log_level: str = None
    web_listen_host: str = None
    web_listen_port: int = None
    web_thread_pool: int = None
    web_ssl_certificate: str = None
    web_ssl_private_key: str = None
    web_ssl_certificate_chain: str = None
    session_max_time: int = None
    login_supported_domain: List[str] = None
    database: Database = None
    ldap_descriptor: LDAP = None
    jinja_env: jinja2.Environment = None

    @staticmethod
    def load():
        dotenv.load_dotenv()

        Config.production = os.getenv('SERVICE_ENVIRONMENT') == 'production'
        Config.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        Config.telegram_bot_url = os.getenv('TELEGRAM_BOT_URL')
        Config.developer_chat_id = os.getenv('DEVELOPER_CHAT_ID')
        Config.log_directory = os.getenv('LOG_DIR')
        Config.log_level = os.environ.get('LOG_LEVEL', logging.DEBUG)
        Config.web_listen_host = os.getenv('WEB_LISTEN_HOST')
        Config.web_listen_port = int(os.getenv('WEB_LISTEN_PORT'))
        Config.web_thread_pool = int(os.getenv('WEB_THREAD_POOL_SIZE', '1'))
        Config.web_ssl_certificate = os.getenv('WEB_SSL_CERTIFICATE')
        Config.web_ssl_private_key = os.getenv('WEB_SSL_PRIVATE_KEY')
        Config.web_ssl_certificate_chain = os.getenv('WEB_SSL_CERTIFICATE_CHAIN')
        Config.session_max_time = int(os.getenv('SESSION_MAX_TIME'))
        Config.database = Database(os.getenv('DATABASE_PATH'))
        Config.ldap_descriptor = LDAP(LDAPConfig.from_env())
        Config.jinja_env = jinja2.Environment(loader=jinja2.PackageLoader('app.web', 'www'))

        login_supported_domain = os.getenv("LOGIN_SUPPORTED_DOMAIN")
        if login_supported_domain is not None:
            Config.login_supported_domain = list(login_supported_domain.split(','))

        if not os.path.exists(Config.log_directory):
            os.mkdir(Config.log_directory)
