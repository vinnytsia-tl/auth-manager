import logging
import os
from typing import List

import dotenv
import jinja2

from app.database import Database
from app.system.ldap import LDAP, LDAPConfig


class Config:
    production: bool
    telegram_bot_token: str
    telegram_bot_url: str
    developer_chat_id: int
    log_directory: str
    log_level: str
    web_listen_host: str
    web_listen_port: int
    web_proxy_base: str
    web_thread_pool: int
    web_static_dir_root_path: str
    web_ssl_certificate: str
    web_ssl_private_key: str
    web_ssl_certificate_chain: str
    session_max_time: int
    login_supported_domain: List[str]
    database: Database
    ldap_descriptor: LDAP
    jinja_env: jinja2.Environment

    @staticmethod
    def __load_env():
        file_path = os.path.realpath(os.path.dirname(__file__))
        app_path = os.path.join(file_path, "..")
        env_path = os.path.join(app_path, ".env")

        dotenv.load_dotenv(dotenv_path=env_path)

    @staticmethod
    def load():
        Config.__load_env()

        Config.production = os.getenv('SERVICE_ENVIRONMENT') == 'production'
        Config.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        Config.telegram_bot_url = os.getenv('TELEGRAM_BOT_URL')
        Config.developer_chat_id = os.getenv('DEVELOPER_CHAT_ID')
        Config.log_directory = os.getenv('LOG_DIR')
        Config.log_level = os.environ.get('LOG_LEVEL', logging.DEBUG)
        Config.web_listen_host = os.getenv('WEB_LISTEN_HOST')
        Config.web_listen_port = int(os.getenv('WEB_LISTEN_PORT'))
        Config.web_proxy_base = os.getenv('WEB_PROXY_BASE')
        Config.web_thread_pool = int(os.getenv('WEB_THREAD_POOL_SIZE', '1'))
        Config.web_static_dir_root_path = os.getenv('WEB_STATIC_DIR_ROOT_PATH')
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
