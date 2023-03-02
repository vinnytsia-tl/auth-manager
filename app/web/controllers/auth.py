import random
import time
import logging
import cherrypy

from app.web.utils import is_authenticated, authenticate, run_tg_send_mgs
from app.config import Config
from app.models import User

logger = logging.getLogger(__name__)


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
    def login(self, username, password):
        if is_authenticated():
            raise cherrypy.HTTPRedirect("/user")

        username_part = username.split('@')
        if len(username_part) == 2:
            if username_part[1] not in Config.login_supported_domain:
                return self.index_template.render(errors=["Домененне ім'я логіну не підтримується"])
            username = Config.ldap_descriptor.normalize_login(username_part[0])
        else:
            username = Config.ldap_descriptor.normalize_login(username)

        if not Config.ldap_descriptor.login(username, password):
            logger.error("Invalid login or password")
            return self.index_template.render(errors=["Неправильний логін або пароль"])

        with Config.database.get_connection() as connection:
            cursor = connection.cursor()
            agent = cherrypy.request.headers.get('User-Agent')
            session_time = time.time()
            exe_str = "DELETE FROM sessions WHERE username = ? OR session_id = ?;"
            cursor.execute(exe_str, [username, cherrypy.session.id])
            exe_str = "INSERT INTO sessions(session_id, username, agent, time) values(?, ?, ?, ?);"
            cursor.execute(
                exe_str, [cherrypy.session.id, username, agent, session_time])

        cherrypy.session['username'] = username
        logger.info(f"User '{username}' successfully logged in")
        raise cherrypy.HTTPRedirect("/user")

    @cherrypy.expose
    def reset(self):
        if is_authenticated():
            raise cherrypy.HTTPRedirect("/user")

        return self.reset_template.render()

    @cherrypy.expose
    def reset_post(self, username, tg_key=None, password=None):
        logger.info("Reset password request received for user: %s", username)
        if is_authenticated():
            raise cherrypy.HTTPRedirect("/user")

        username_part = username.split('@')
        if len(username_part) == 2:
            if username_part[1] not in Config.login_supported_domain:
                return self.reset_template.render(errors=["Домененне ім'я логіну не підтримується"])
            username = Config.ldap_descriptor.normalize_login(username_part[0])
        else:
            username = Config.ldap_descriptor.normalize_login(username)

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
                else:
                    logger.error(
                        "Error saving password for user: %s", username)
                    return self.reset_template.render(
                        errors=["Помилка збереження паролю, можливо він не відповідає вимогам."])
            else:
                logger.error("Incorrect reset token for user: %s", username)
                return self.reset_template.render(errors=["Хибний код підтвердження, спробуйте ще раз."])
        else:
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
