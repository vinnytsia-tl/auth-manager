import base64
import logging
import random
from io import BytesIO

import cherrypy
import qrcode

import app.models
from app.config import Config
from app.web.utils import authenticate, run_tg_send_mgs

logger = logging.getLogger(__name__)


class User():
    def __init__(self):
        self.index_template = Config.jinja_env.get_template('user/index.html')
        self.reset_info_template = Config.jinja_env.get_template(
            'user/reset_info.html')
        self.telegram_new_template = Config.jinja_env.get_template(
            'user/telegram_new.html')

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['GET'])
    @authenticate
    def index(self):
        user = app.models.User.find(cherrypy.session['username'])
        params = {'user': user}
        logger.info("User '%s' accessed index page.", user.name)
        return self.index_template.render(params)

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['GET'])
    @authenticate
    def reset_info(self):
        user = app.models.User.find(cherrypy.session['username'])
        params = {'user': user}
        logger.info("User '%s' accessed reset_info page.", user.name)
        return self.reset_info_template.render(params)

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['GET'])
    @authenticate
    def telegram_new(self):
        user = app.models.User.find(cherrypy.session['username'])
        user.bind_token = random.randrange(1_000_000, 9_999_999)
        user.save()

        start_data = base64.b64encode(
            f"{user.login} {user.bind_token}".encode()).decode()

        if len(start_data) <= 64:
            logger.info(
                "Generate full_token for '%s' user, start_data len = %d", user.name, len(start_data))
            full_tg_url = f"{Config.telegram_bot_url}?start={start_data}"
        else:
            logger.warning(
                "Can't generate full_token for '%s' user, start_data len = %d", user.name, len(start_data))
            full_tg_url = Config.telegram_bot_url

        buffer = BytesIO()
        img = qrcode.make(full_tg_url)
        img.save(buffer)
        encoded_img = base64.b64encode(buffer.getvalue()).decode()
        img_qr_data = "data:image/png;base64,{}".format(encoded_img)

        params = {'user': user, 'tg_url': Config.telegram_bot_url,
                  'full_tg_url': full_tg_url, 'img_qr_data': img_qr_data}
        logger.info("User '%s' accessed telegram_new page.", user.name)
        return self.telegram_new_template.render(params)

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['GET'])
    @authenticate
    def telegram_destroy(self):
        user = app.models.User.find(cherrypy.session['username'])
        if user.telegram is not None:
            tg_id = user.telegram
            user.telegram = None
            user.save()

            run_tg_send_mgs(
                tg_id, f"Інтеграцію для користувача {user.name} скасовано")

        logger.info("User '%s' destroyed telegram integration.", user.name)
        raise cherrypy.HTTPRedirect("/user/reset_info")
