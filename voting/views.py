from mako.template import Template

from voting.context import context
from voting.data_interactions import get_list_of_teams
from voting.data_interactions import get_list_of_users
from voting.data_interactions import get_user
from voting.data_interactions import get_users_not_assigned_to_teams


def AdminView():
    return Template(filename='voting/static/admin.html').render(
        title=context.app_name,
        users=get_list_of_users(),
        get_user=get_user,
        teams=list(context.redis.smembers('teams')),
        unassigned_users=get_users_not_assigned_to_teams
    )

def LoginView(*args, error=None, **kw):
    print(error)
    return Template(filename='voting/static/login.html').render(title=context.app_name)


def WelcomeView():
    return Template(filename='voting/static/index.html').render(title=context.app_name)


def RegisterView():
    return Template(filename='voting/static/register.html').render(
        title=context.app_name,
        teams=get_list_of_teams()
    )
