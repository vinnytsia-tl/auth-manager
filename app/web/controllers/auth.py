import logging
import random
from typing import Optional

import cherrypy
import pyotp

from app.common.web.utils import is_authenticated, save_session
from app.config import Config
from app.models import User, UserBindDestination
from app.web.utils import run_tg_send_msg

logger = logging.getLogger(__name__)


class Auth():
    def __init__(self):
        self.index_template = Config.jinja_env.get_template('auth/index.html')
        self.reset_template = Config.jinja_env.get_template('auth/reset.html')
        self.reset_typed_template = Config.jinja_env.get_template('auth/reset_typed.html')

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
    @cherrypy.tools.allow(methods=['POST'])
    @cherrypy.tools.normalize_username()
    def reset_post(self, username: str, errors: Optional[list[str]] = None):
        if is_authenticated():
            raise cherrypy.HTTPRedirect("/user")

        user = User.try_find(username)
        if user is None:
            logger.error("User not found: %s", username)
            return self.reset_template.render(errors=["Користувача не знайдено."])

        bind_dest_list = []
        if user.email2 is not None:
            bind_dest_list.append(UserBindDestination.EMAIL)
        if user.phone is not None:
            bind_dest_list.append(UserBindDestination.PHONE)
        if user.telegram is not None:
            bind_dest_list.append(UserBindDestination.TELEGRAM)
        if user.otp is not None:
            bind_dest_list.append(UserBindDestination.OTP)

        return self.reset_template.render(user=user, type_form=True, bind_dest_list=bind_dest_list)

    @cherrypy.expose
    @cherrypy.tools.normalize_username()
    def reset_typed(self, username: str, bind_dest_id: str, errors: Optional[list[str]] = None):
        if is_authenticated():
            raise cherrypy.HTTPRedirect("/user")

        user = User.try_find(username)
        if user is None:
            logger.error("User not found: %s", username)
            return self.reset_template.render(errors=["Користувача не знайдено."])

        bind_dest = UserBindDestination(int(bind_dest_id))

        if bind_dest == UserBindDestination.OTP:
            logger.info("Reset via OTP for user: %s", username)
        elif bind_dest == UserBindDestination.TELEGRAM:
            if user.telegram is not None:
                user.reset_token = random.randrange(1_000_000, 9_999_999)
                user.save()

                run_tg_send_msg(user.telegram, f"Ваш код підтвердження {user.reset_token}")
                logger.info("Reset token sent via telegram for user: %s", username)
            else:
                return self.reset_template.render(errors=["Щось пішло не так, спробуйте ще раз."])

        return self.reset_typed_template.render(username=user.login, bind_dest_id=bind_dest.value)

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])
    @cherrypy.tools.normalize_username()
    def reset_save(self, username: str, bind_dest_id: str, reset_key: str, password: str, errors=None):
        logger.info("Reset password request received for user: %s", username)
        if is_authenticated():
            raise cherrypy.HTTPRedirect("/user")

        if errors is not None:
            return self.reset_typed_template.render(errors=errors)

        user = User.try_find(username)
        if user is None:
            logger.error("User not found: %s", username)
            return self.reset_typed_template.render(username=username,
                                                    bind_dest_id=bind_dest_id,
                                                    errors=["Користувача не знайдено."])

        bind_dest = UserBindDestination(int(bind_dest_id))
        if bind_dest == UserBindDestination.OTP and user.otp is not None:
            otp_valid = pyotp.totp.TOTP(user.otp).verify(reset_key)
            if otp_valid:
                if Config.ldap_descriptor.set_password(username, password):
                    logger.info("Password reset successful for user: %s", username)
                    raise cherrypy.HTTPRedirect("/auth")

                logger.error("Error saving password for user: %s", username)
                return self.reset_typed_template.render(
                    username=username,
                    bind_dest_id=bind_dest_id,
                    errors=["Помилка збереження паролю, можливо він не відповідає вимогам."])
            else:
                logger.error("Incorrect OTP for user: %s", username)
                return self.reset_typed_template.render(username=username,
                                                        bind_dest_id=bind_dest_id,
                                                        errors=["Хибний код підтвердження, спробуйте ще раз."])
        elif bind_dest == UserBindDestination.TELEGRAM and user.telegram is not None:
            if reset_key is not None and reset_key.isnumeric() is True and \
               user.reset_token == int(reset_key) and str(user.reset_token) == reset_key:
                user.reset_token = None
                user.save()

                if Config.ldap_descriptor.set_password(username, password):
                    logger.info("Password reset successful for user: %s", username)
                    raise cherrypy.HTTPRedirect("/auth")

                logger.error("Error saving password for user: %s", username)
                return self.reset_typed_template.render(
                    username=username,
                    bind_dest_id=bind_dest_id,
                    errors=["Помилка збереження паролю, можливо він не відповідає вимогам."])

            logger.error("Incorrect telegram reset token for user: %s", username)
            return self.reset_typed_template.render(username=username,
                                                    bind_dest_id=bind_dest_id,
                                                    errors=["Хибний код підтвердження, спробуйте ще раз."])

        return self.reset_typed_template.render(username=username,
                                                bind_dest_id=bind_dest_id,
                                                errors=["Щось пішло не так, почни зпочатку."])

    @cherrypy.expose
    @cherrypy.tools.authenticate()
    def logout(self):
        with Config.database.get_connection() as connection:
            connection.execute(
                'DELETE FROM sessions WHERE session_id = ?;', (cherrypy.session.id,))

        cherrypy.session['username'] = None
        raise cherrypy.HTTPRedirect("/auth")
