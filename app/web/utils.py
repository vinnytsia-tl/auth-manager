from __future__ import annotations
from typing import Callable
import time
import cherrypy

import asyncio
from telegram.ext import ApplicationBuilder

from app.config import Config


def is_authenticated():
    agent = cherrypy.request.headers.get('User-Agent')
    session_time = time.time() - Config.session_max_time
    exe_str = "SELECT 1 FROM sessions WHERE session_id = ? AND agent = ? AND time > ?;"
    cursor = Config.database.execute(
        exe_str, (cherrypy.session.id, agent, session_time))
    return cursor.fetchone() is not None


def authenticate(func: Callable[..., any]):
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            raise cherrypy.HTTPRedirect("/auth")
        return func(*args, **kwargs)

    return wrapper


async def tg_send_msg(chat_id, text):
    application = ApplicationBuilder().token(Config.telegram_bot_token).build()
    await application.bot.sendMessage(chat_id=chat_id, text=text)


def run_tg_send_mgs(chat_id, text):
    asyncio.run(tg_send_msg(chat_id, text))
