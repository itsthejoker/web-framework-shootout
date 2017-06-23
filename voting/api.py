import cherrypy
from decorator import decorator

from voting.data_interactions import add_event
from voting.data_interactions import add_team
from voting.data_interactions import create_new_user
from voting.data_interactions import delete_event
from voting.data_interactions import delete_team
from voting.data_interactions import edit_event
from voting.data_interactions import get_event
from voting.data_interactions import get_list_of_teams
from voting.data_interactions import get_team
from voting.data_interactions import get_user
from voting.data_interactions import update_user
from voting.helpers import session
from voting.helpers import validate_admin
from voting.helpers import validate_password

__all__ = ['api']

"""
In CherryPy, routing is handled by a combination of the conf and the actual
structure of the classes. For example:

'/api/login': {
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.response_headers.on': True,
        'tools.response_headers.headers': [('Content-Type', 'application/json')],
    },

...in conf requires adding both the api class and the login class, in order, to
the app being run. For example:

app = App()
app.api = API()
app.api.login = api_login()

cherrypy.quickstart(app, '/', conf)

Here, we're setting up the entire API tree before it gets imported by main.py.
That allows us to modify anything we need here without having to deal with it
in the main file.
"""

@decorator
def api_login_required(f, *args, **kw):
    if not session.is_authenticated():
        return {
            'result': 'error',
            'response': 'Login is required. Send username and password to /api/login and try again.'
        }
    else:
        return f(*args, **kw)

@decorator
def api_admin_required(f, *args, **kw):
    if not session.is_admin():
        return {
            'result': 'error',
            'response': 'Only an administrator can perform this action.'
        }
    return f(*args, **kw)

@cherrypy.expose
class api_login(object):
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        username = cherrypy.request.json.get('username', None)
        password = cherrypy.request.json.get('password', None)

        if username and password:
            # try and authenticate
            if validate_password(username, password):
                session.is_authenticated(update_to=True)
                if validate_admin(username, password):
                    session.is_admin(update_to=True)
                return {'result': 'success'}
            else:
                return {'result': 'error'}

        return {
            'result': 'error',
            'response': 'This endpoint requires a json dict with the keys `username` and `password`.'
        }


@cherrypy.expose
class api_logout(object):
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        session.is_authenticated(update_to=False)
        session.is_admin(update_to=False)
        return {'result': 'success'}


@cherrypy.expose
class api_user(object):
    """
    Returns the requested user entry.
    """
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        username = cherrypy.request.json.get('username', None)
        if username:
            return get_user(username)
        else:
            return {'result': 'error', 'response': 'Requires username to fetch'}


@cherrypy.expose
class api_user_update(object):
    @api_login_required
    @api_admin_required
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        username = cherrypy.request.json.get('username', None)
        password = cherrypy.request.json.get('password', None)
        team = cherrypy.request.json.get('team', None)
        name = cherrypy.request.json.get('name', None)
        admin = False
        if not username:
            return {'result': 'error', 'response': 'Updating a user requires a username.'}
        if any([password, team, name, admin]):
            update_user(username, password=password, name=name, team=team, admin=admin)
            return {'result': 'success'}


@cherrypy.expose
class api_user_create(object):
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        username = cherrypy.request.json.get('username', None)
        password = cherrypy.request.json.get('password', None)
        team = cherrypy.request.json.get('team', None)
        name = cherrypy.request.json.get('name', None)
        admin = cherrypy.request.json.get('admin', False)

        if username and password:
            result = create_new_user(
                username=username,
                password=password,
                team=team,
                name=name,
                admin=admin
            )
            return {'result': 'success'} if result else {'result': 'error', 'response': 'user already exists'}
        else:
            return {'result': 'Not enough information received. Requires at least {\'username\': "", \'password\': ""}'
                              ' to create a new user.'}


@cherrypy.expose
class api_user_admin(object):
    @api_login_required
    @api_admin_required
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        username = cherrypy.request.json.get('username', None)
        admin = cherrypy.request.json.get('admin', None)
        if not username:
            return {'result': 'error', 'response': 'Updating a user requires a username.'}
        if admin is True or admin is False:  # basically, is it in the request at all?
            update_user(username, None, None, None, admin)
            return {'result': 'success'}


@cherrypy.expose
class api_teams(object):
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        return {'result': 'success', 'response': {'teams': get_list_of_teams()}}


@cherrypy.expose
class api_teams_get(object):
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        team = cherrypy.request.json.get('team', None) or cherrypy.request.json.get('name', None)
        if team:
            result = get_team(team)
            if result:
                return {'result': 'success', 'response': result}
            else:
                return {'result': 'error', 'response': 'Could not find team by that name.'}
        return {'result': 'error', 'response': 'Must have team name to look up team by.'}


@cherrypy.expose
class api_teams_create(object):
    @api_login_required
    @api_admin_required
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        team = cherrypy.request.json.get('team', None) or cherrypy.request.json.get('name', None)
        result = add_team(team)
        if result:
            return {'result': 'success', 'response': f'Team {team} created.'}
        return {'result': 'error', 'response': f'Team {team} already exists.'}


@cherrypy.expose
class api_teams_delete(object):
    @api_login_required
    @api_admin_required
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        team = cherrypy.request.json.get('team', None)
        result = delete_team(team)
        if result:
            return {'result': 'success', 'response': f'Team {team} deleted.'}
        else:
            return {'result': 'error', 'response': f'Team {team} does not exist.'}


@cherrypy.expose
class api_event(object):
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        name = cherrypy.request.json.get('name', None) or cherrypy.request.json.get('title', None)
        if name:
            return get_event(name)
        else:
            return {'result': 'error', 'response': 'This endpoint requires a `name` or `title` attribute.'}


@cherrypy.expose
class api_event_create(object):
    @api_login_required
    @api_admin_required
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        name = cherrypy.request.json.get('name', None)
        start_date = cherrypy.request.json.get('start_date', None)
        end_date = cherrypy.request.json.get('end_date', None)
        categories = cherrypy.request.json.get('categories', None)

        result = add_event(name, start_date=start_date, end_date=end_date, categories=categories)

        if result:
            return {'result': 'success', 'response': f'The event {name} has been created.'}
        else:
            return {'result': 'error', 'response': f'The event {name} already exists!'}


@cherrypy.expose
class api_event_edit(object):
    @api_login_required
    @api_admin_required
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        name = cherrypy.request.json.get('name', None)
        new_name = cherrypy.request.json.get('new_name', None)
        start_date = cherrypy.request.json.get('start_date', None)
        end_date = cherrypy.request.json.get('end_date', None)
        categories = cherrypy.request.json.get('categories', None)

        if name:
            result = edit_event(name, new_name, start_date, end_date, categories)
            if result:
                return {'result': 'success', 'response': f'The event {name} has been edited.'}
            else:
                return {'result': 'error', 'response': f'The event {name} does not exist!'}
        else:
            return {'result': 'error', 'response': 'This endpoint requires a `name` attribute.'}


@cherrypy.expose
class api_event_delete(object):
    @api_login_required
    @api_admin_required
    @cherrypy.tools.accept(media='application/json')
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):
        name = cherrypy.request.json.get('name', None)
        if name:
            result = delete_event(name)
            if result:
                return {'result': 'success', 'response': f'The event {name} has been deleted.'}
            else:
                return {'result': 'error', 'response': f'The event {name} does not exist!'}
        else:
            return {'result': 'error', 'response': 'This endpoint requires a `name` attribute.'}


@cherrypy.expose
class API_BASE(object):
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    @cherrypy.tools.accept(media='application/json')
    def GET(self):
        return 'Please use the actual endpoints'

    def POST(self):
        return 'Please use the actual endpoints'

# build the actual API tree
api = API_BASE()

api.login = api_login()

api.user = api_user()
api.user.update = api_user_update()
api.user.create = api_user_create()
api.user.admin = api_user_admin()

api.teams = api_teams()
api.teams.create = api_teams_create()
api.teams.delete = api_teams_delete()
api.teams.get = api_teams_get()

api.event = api_event()
api.event.create = api_event_create()
api.event.delete = api_event_delete()
api.event.edit = api_event_edit()
