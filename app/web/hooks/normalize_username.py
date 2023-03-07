from cherrypy import request

from app.config import Config


def normalize_username():
    if "username" not in request.params:
        return

    username = request.params['username']
    username_part = username.split('@')
    if len(username_part) == 2:
        if username_part[1] not in Config.login_supported_domain:
            request.params['errors'] = [
                "Домененне ім'я логіну не підтримується"]
            return
        request.params['username'] = Config.ldap_descriptor.normalize_login(
            username_part[0])
    else:
        request.params['username'] = Config.ldap_descriptor.normalize_login(
            username)
