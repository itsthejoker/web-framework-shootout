from os.path import abspath

import cherrypy

from voting.helpers import validate_admin
from voting.helpers import validate_password

api_endpoint = {
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [('Content-Type', 'application/json')],
    }

conf = {
    '/': {
        'tools.sessions.on': True
    },
    # '/app': {
    #     'tools.auth_basic.on': True,
    #     'tools.auth_basic.realm': 'localhost',
    #     'tools.auth_basic.checkpassword': validate_password
    #  },
    #  '/admin': {
    #      'tools.auth_basic.on': True,
    #      'tools.auth_basic.realm': 'localhost',
    #      'tools.auth_basic.checkpassword': validate_admin
    #  },
    # For all static directories, staticdir needs an absolute path
    # This is easily one of the most confusing things starting out
    # about CherryPy
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': abspath('./voting/static')
    },
    '/css': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': abspath('./voting/static/css')
    },
    '/js': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': abspath('./voting/static/js')
    },
    '/fonts': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': abspath('./voting/static/fonts')
    },
    '/plugins/DataTables': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': abspath('./voting/static/plugins/DataTables')
    },
    '/api': api_endpoint,
    '/api/login': api_endpoint,
    # '/api/user': api_endpoint,
    # '/api/user/update': api_endpoint,
    # '/api/user/create': api_endpoint,
    # '/api/user/admin': api_endpoint,
}
