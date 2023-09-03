import base64
import html
import json
import logging
import traceback
from enum import Enum, auto, unique

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from ..config import Config
from ..models import User, UserBindDestination
from . import resources

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:",
                 exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_msg = context.error.__traceback__ if context.error is not None else None
    tb_list = traceback.format_exception(None, context.error, tb_msg)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    # max message size 4096
    await context.bot.send_message(
        chat_id=Config.developer_chat_id, text=message[:4000], parse_mode=ParseMode.HTML
    )


@unique
class StartConversationState(Enum):
    LOGIN = auto()
    CONFIRMATION = auto()
    FINISH = auto()


async def sc_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> StartConversationState | int:
    logger.debug("sc_start %s", update)

    if update.message is None or update.message.text is None:
        logger.error("sc_start with message/text None")
        return StartConversationState.LOGIN

    user = User.try_find_by_telegram(update.message.chat.id)
    if user is not None:
        await update.message.reply_text(resources.SC_START_DONE_TEXT % user.name)
        return ConversationHandler.END

    data = update.message.text.split()
    if len(data) > 1:
        login, bind_token = base64.b64decode(data[1]).decode().split()
        user = User.try_find(login)
        if user is None:
            await update.message.reply_text(resources.SC_LOGIN_ERROR_TEXT)
            await update.message.reply_text(resources.SC_START_OK_TEXT)
            return StartConversationState.LOGIN

        if user.bind_token != bind_token or user.bind_dest != UserBindDestination.TELEGRAM:
            if user.bind_dest != UserBindDestination.TELEGRAM:
                await update.message.reply_text(resources.SC_CONFIRMATION_NTG_ERROR_TEXT)
            else:
                await update.message.reply_text(resources.SC_CONFIRMATION_ERROR_TEXT)
            await update.message.reply_text(resources.SC_START_OK_TEXT)
            user.bind_token = None
            user.bind_dest = UserBindDestination.NONE
            user.save()
            return StartConversationState.LOGIN

        assert context.chat_data is not None
        context.chat_data['login'] = login
        context.chat_data['tg_id'] = update.message.chat.id

        text = resources.SC_FINISH_TEXT % user.name
        await update.message.reply_text(text, reply_markup=resources.SC_SET_USERNAME_MARKUP)
        return StartConversationState.FINISH

    await update.message.reply_text(resources.SC_START_OK_TEXT)
    return StartConversationState.LOGIN


async def sc_set_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> StartConversationState:
    logger.debug("sc_set_login %s", update)

    if update.message is None or update.message.text is None:
        logger.error("sc_set_login with message/text None")
        return StartConversationState.LOGIN

    login = update.message.text.strip()
    user = User.try_find(login)
    if user is None:
        await update.message.reply_text(resources.SC_LOGIN_ERROR_TEXT)
        await update.message.reply_text(resources.SC_START_OK_TEXT)
        return StartConversationState.LOGIN

    if user.bind_token is None:
        await update.message.reply_text(resources.SC_CONFIRMATION_NONE_TEXT)
        await update.message.reply_text(resources.SC_START_OK_TEXT)
        return StartConversationState.LOGIN

    assert context.chat_data is not None
    context.chat_data['login'] = login
    await update.message.reply_text(resources.SC_CONFIRMATION_OK_TEXT)
    return StartConversationState.CONFIRMATION


async def sc_set_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> StartConversationState:
    logger.debug("sc_set_confirmation %s", update)

    if update.message is None or update.message.text is None:
        logger.error("sc_set_confirmation with message/text None")
        return StartConversationState.LOGIN

    assert context.chat_data is not None
    user = User.find(context.chat_data['login'])
    bind_token = update.message.text.strip()

    if user.bind_token != bind_token:
        await update.message.reply_text(resources.SC_CONFIRMATION_ERROR_TEXT)
        await update.message.reply_text(resources.SC_START_OK_TEXT)

        user.bind_token = None
        user.save()

        return StartConversationState.LOGIN

    user.bind_token = None
    user.save()

    context.chat_data['tg_id'] = update.message.chat.id

    text = resources.SC_FINISH_TEXT % user.name
    await update.message.reply_text(text, reply_markup=resources.SC_SET_USERNAME_MARKUP)
    return StartConversationState.FINISH


async def sc_save_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> StartConversationState | int:
    logger.debug("sc_save_user %s", update)

    if update.callback_query is None or update.callback_query.message is None:
        logger.error("sc_save_user with callback_query/message None")
        return StartConversationState.LOGIN

    assert context.chat_data is not None
    user = User.find(context.chat_data['login'])
    user.telegram = context.chat_data['tg_id']
    user.save()

    await update.callback_query.message.edit_text(resources.SC_SAVE_USER_TEXT)
    return ConversationHandler.END


async def sc_reset_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> StartConversationState:
    logger.debug("sc_reset_user %s", update)

    if context.chat_data is not None:
        context.chat_data.clear()

    if update.callback_query is not None and update.callback_query.message is not None:
        await update.callback_query.message.edit_text(resources.SC_START_OK_TEXT)

    return StartConversationState.LOGIN


async def help_cmd(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.debug("help_cmd %s", update)

    if update.message is None:
        logger.error("help_cmd with message None")
        return

    await update.message.reply_text(resources.HELP_TEXT)


async def whoami(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.debug("whoami %s", update)

    if update.message is None:
        logger.error("whoami with message None")
        return

    user = User.try_find_by_telegram(update.message.chat_id)
    if user is None:
        await update.message.reply_text(resources.WHOAMI_NONE_TEXT)
    else:
        await update.message.reply_text(resources.WHOAMI_USER_TEXT % (user.login, user.name))
