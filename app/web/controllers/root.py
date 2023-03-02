import cherrypy

from app.web.utils import is_authenticated


class Root():
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("/user" if is_authenticated() else "/auth")
