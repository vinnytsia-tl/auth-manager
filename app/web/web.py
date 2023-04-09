import logging

import cherrypy

from app.config import Config

from .controllers import Auth, Office365, Root, User

logger = logging.getLogger(__name__)


def get_cherrypy_config():
    return {
        '/': {
            'tools.secureheaders.on': True,
            'tools.sessions.on': True,
            'tools.sessions.httponly': True,
            'tools.staticdir.root': Config.web_static_dir_root_path,
            'tools.trailing_slash.on': False,
            'tools.response_headers.on': True,
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './static',
        },
    }


def enable_ssl():
    if Config.web_ssl_certificate is None:
        logger.info('SSL certificate is not specified. Run server in HTTP mode.')
        return

    if Config.web_ssl_private_key is None:
        logger.info('SSL private key is not specified. Run server in HTTP mode.')
        return

    cherrypy.server.ssl_module = 'builtin'
    cherrypy.server.ssl_certificate = Config.web_ssl_certificate
    cherrypy.server.ssl_private_key = Config.web_ssl_private_key

    if Config.web_ssl_certificate_chain is not None:
        logger.debug('SSL certificate chain is not specified.')
        cherrypy.server.ssl_certificate_chain = Config.web_ssl_certificate_chain


class Web:
    @staticmethod
    def start():
        logger.info('Starting web server...')

        app = Root()
        app.auth = Auth()
        app.user = User()
        app.office365 = Office365()

        logger.debug("Created app controllers.")

        server_config = {
            'server.socket_host': Config.web_listen_host,
            'server.socket_port': Config.web_listen_port,
            'server.thread_pool': Config.web_thread_pool,
            'engine.autoreload.on': not Config.production,
            'engine.autoreload.frequency': 1,
            'log.screen': not Config.production,
            'log.screen.level': Config.log_level,
            'log.error_file': Config.log_directory + '/web_error.log',
            'log.access_file': Config.log_directory + '/web_access.log',
        }

        if Config.web_proxy_base is not None:
            server_config['tools.proxy.on'] = True
            server_config['tools.proxy.base'] = Config.web_proxy_base

        cherrypy.config.update(server_config)
        enable_ssl()
        logger.debug('Web server config updated.')

        config = get_cherrypy_config()
        if Config.production:
            config['/']['tools.sessions.secure'] = True

        cherrypy.engine.subscribe('start', Config.database.cleanup)
        logger.debug('Web engine subscribed.')
        cherrypy.tree.mount(app, '/', config)
        logger.debug('Web tree mounted.')
        cherrypy.engine.start()
        logger.info('Web server started.')
        cherrypy.engine.block()

    @staticmethod
    def stop():
        cherrypy.engine.exit()

    @staticmethod
    @cherrypy.tools.register('before_finalize', priority=60)
    def secureheaders():
        logger.debug('Execute secureheaders hook')

        headers = cherrypy.response.headers
        headers['X-Frame-Options'] = 'DENY'
        headers['X-XSS-Protection'] = '1; mode=block'
        if Config.production:
            headers['Content-Security-Policy'] = '''
                default-src 'self' https;
                font-src 'self' data: fonts.gstatic.com;
                style-src 'self' fonts.googleapis.com;
                img-src 'self' data:;
            '''
