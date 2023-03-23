import logging

from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ConversationHandler, MessageHandler, filters)

from app.config import Config

from . import handlers
from .handlers import StartConversationState

logger = logging.getLogger(__name__)


class Bot:
    def __init__(self) -> None:
        logger.info("Initializing bot")
        self.application = Application.builder().token(Config.telegram_bot_token).build()
        self.__register_handlers__()

    def __register_handlers__(self) -> None:
        logger.info("Registering handlers")
        self.application.add_handler(ConversationHandler(
            entry_points=[CommandHandler(
                'start', handlers.sc_start, block=False)],
            states={
                StartConversationState.LOGIN: [
                    MessageHandler(
                        filters.TEXT, handlers.sc_set_login, block=False)
                ],
                StartConversationState.CONFIRMATION: [
                    MessageHandler(
                        filters.TEXT, handlers.sc_set_confirmation, block=False)
                ],
                StartConversationState.FINISH: [
                    CallbackQueryHandler(
                        handlers.sc_save_user, pattern='^save$', block=False),
                    CallbackQueryHandler(
                        handlers.sc_reset_user, pattern='^reset$', block=False),
                ],
            },
            fallbacks=[],
        ))
        self.application.add_handler(CommandHandler(
            'whoami', handlers.whoami, block=False))
        self.application.add_handler(CommandHandler(
            'help', handlers.help, block=False))

        logger.debug("Registering error handlers")
        self.application.add_error_handler(handlers.error_handler)

    def start(self) -> None:
        logger.info('Starting bot polling')
        self.application.run_polling()

    def stop(self) -> None:
        logger.info('Stopping bot')
        self.application.stop()
