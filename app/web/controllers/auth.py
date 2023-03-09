import logging
import random

import cherrypy

from app.config import Config
from app.models import User
from app.web.hooks import normalize_username
from app.web.utils import (authenticate, is_authenticated, run_tg_send_mgs,
                           save_session)

logger = logging.getLogger(__name__)

cherrypy.tools.normalize_username = cherrypy.Tool(
    'before_handler', normalize_username)


class Auth():
    def __init__(self):
        self.index_template = Config.jinja_env.get_template('auth/index.html')
        self.reset_template = Config.jinja_env.get_template('auth/reset.html')

    @cherrypy.expose
    def index(self):
        if is_authenticated():
            raise cherrypy.HTTPRedirect("/user")

        return self.index_template.render()

    @cherrypy.expose
    @cherrypy.tools.normalize_username()
    def login(self, username, password, errors=None):
        if is_authenticated():
            raise cherrypy.HTTPRedirect("/user")

        if errors is not None:
            return self.index_template.render(errors=errors)

        if not Config.ldap_descriptor.login(username, password):
            logger.error("Invalid login or password")
            return self.index_template.render(errors=["Неправильний логін або пароль"])

        save_session(username)

        cherrypy.session['username'] = username
        logger.info("User '%s' successfully logged in", username)
        raise cherrypy.HTTPRedirect("/user")

    @cherrypy.expose
    def reset(self):
        if is_authenticated():
            raise cherrypy.HTTPRedirect("/user")

        return self.reset_template.render()

    @cherrypy.expose
    @cherrypy.tools.normalize_username()
    def reset_post(self, username, tg_key=None, password=None, errors=None):
        logger.info("Reset password request received for user: %s", username)
        if is_authenticated():
            raise cherrypy.HTTPRedirect("/user")

        if errors is not None:
            return self.reset_template.render(errors=errors)

        user = User.find(username)
        if user is None:
            logger.error("User not found: %s", username)
            return self.reset_template.render(errors=["Користувача не знайдено."])

        if user.telegram is None:
            logger.error("Telegram not linked for user: %s", username)
            return self.reset_template.render(errors=["Телеграм аккаунт не прив'язано. Скинути пароль неможливо."])

        if tg_key is not None:
            if tg_key.isnumeric() is True and user.reset_token == int(tg_key) and str(user.reset_token) == tg_key:
                user.reset_token = None
                user.save()

                if Config.ldap_descriptor.set_password(username, password):
                    logger.info(
                        "Password reset successful for user: %s", username)
                    raise cherrypy.HTTPRedirect("/auth")

                logger.error(
                    "Error saving password for user: %s", username)
                return self.reset_template.render(
                    errors=["Помилка збереження паролю, можливо він не відповідає вимогам."])

            logger.error("Incorrect reset token for user: %s", username)
            return self.reset_template.render(errors=["Хибний код підтвердження, спробуйте ще раз."])

        user.reset_token = random.randrange(1_000_000, 9_999_999)
        user.save()

        run_tg_send_mgs(user.telegram,
                        f"Ваш код підтвердження {user.reset_token}")
        logger.info(
            "Reset token sent via telegram for user: %s", username)

        params = {'form2': True, 'tg_key': True, 'username': username}
        return self.reset_template.render(params)

    @cherrypy.expose
    @authenticate
    def logout(self):
        with Config.database.get_connection() as connection:
            connection.execute(
                'DELETE FROM sessions WHERE session_id = ?;', (cherrypy.session.id,))

        cherrypy.session['username'] = None
        raise cherrypy.HTTPRedirect("/auth")
