import cherrypy

from app.config import Config



class Office365():
    def __init__(self):
        self.index_template = Config.jinja_env.get_template('office365/index.html')

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['GET'])
    def index(self):
        return self.index_template.render()
