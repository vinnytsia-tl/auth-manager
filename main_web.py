import os
import logging

from app.web import Web
from app.config import Config
from app.database.migrations import apply_migrations


def setup_app_logger():
    logger = logging.getLogger('app')
    logger.setLevel(Config.log_level)
    formatter = logging.Formatter('[%(asctime)s] #%(thread)d [%(levelname)s] %(name)s: %(message)s', datefmt='%d/%b/%Y:%H:%M:%S')

    # create a StreamHandler to log to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(Config.log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # create a FileHandler to log to a file
    file_handler = logging.FileHandler(os.path.join(Config.log_directory, 'app_web.log'))
    file_handler.setLevel(Config.log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


if __name__ == '__main__':
    Config.load()
    setup_app_logger()
    apply_migrations()
    Web.start()
