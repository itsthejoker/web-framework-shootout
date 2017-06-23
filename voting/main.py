# noinspection PyUnresolvedReferences
import better_exceptions
import cherrypy
from decorator import decorator

from voting import conf
from voting.api import api
from voting.helpers import session
from voting.helpers import validate_admin
from voting.helpers import validate_password
from voting.views import AdminView
from voting.views import LoginView
from voting.views import RegisterView
from voting.views import WelcomeView


@decorator
def login_required(f, *args, **kw):
    if session.is_authenticated():
        # we have fulfilled our mission. Give them what they want.
        return f(*args, **kw)
    # Is this a request coming back from a login page?
    username = session.get_username()
    password = session.get_password()
    if username and password:
        # looks like it is, so try and authenticate.
        if validate_password(username, password):
            session.is_authenticated(update_to=True)
            if validate_admin(username, password):
                session.is_admin(update_to=True)
            return f(*args, **kw)
        else:
            # authentication failed
            LoginView(*args, **kw)
    else:
        # we don't already have login information, so let's send the login page
        return LoginView()

class App(object):
    @cherrypy.expose
    @cherrypy.tools.json_in()
    def index(self):
        return WelcomeView()

    @cherrypy.expose
    def register(self):
        return RegisterView()

    @cherrypy.expose
    @login_required
    def admin(self, **kwargs):
        return AdminView()


    @cherrypy.expose
    @login_required
    def app(self):
        return "snarfleblat"

thingy = App()
thingy.api = api

cherrypy.quickstart(thingy, '/', conf)
# cherrypy.quickstart(App(), '/', conf)
