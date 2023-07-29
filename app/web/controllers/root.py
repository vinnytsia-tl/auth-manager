import logging

import cherrypy

from app.common.web.utils import is_authenticated

from .auth import Auth
from .office365 import Office365
from .user import User

logger = logging.getLogger(__name__)


class Root():
    def __init__(self) -> None:
        self.auth = Auth()
        self.user = User()
        self.office365 = Office365()
        logger.debug("Created app controllers")

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/user" if is_authenticated() else "/auth")
