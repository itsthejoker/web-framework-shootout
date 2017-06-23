import pickle

from addict import Dict

from voting.context import context
from voting.helpers import hash_password


# *************************************
#   _    _  _____ ______ _____   _____
#  | |  | |/ ____|  ____|  __ \ / ____|
#  | |  | | (___ | |__  | |__) | (___
#  | |  | |\___ \|  __| |  _  / \___ \
#  | |__| |____) | |____| | \ \ ____) |
#   \____/|_____/|______|_|  \_\_____/
# *************************************

# teams: set of all team names
# team_name: set of all users on that team
# username: pickled dict of all user attributes

def get_list_of_users():
    return list(context.redis.smembers('users'))


def create_new_user(username, password, team=None, name=None, admin=False):
    password = hash_password(password)

    user = Dict()
    user.username = username
    user.password = password
    user.force_password_reset = True
    user.name = name
    user.team = team
    user.vote = None
    user.admin = admin

    result = context.redis.sadd('users', username)
    if result == 0:
        # user is already there
        return False
    context.redis.set(username, pickle.dumps(user.to_dict()))

    if team:
        add_user_to_team(username, team)
    if admin:
        context.redis.sadd('admins', username)
    return True


def get_user(username, include_password=False):
    user = pickle.loads(context.redis.get(username))

    # DICT COMPREHENSIONS, MOFO
    user = {k:str(v) for k, v in user.items()}
    if not include_password:
        del user['password']

    return user


def delete_user(username):
    context.redis.delete(username)
    context.redis.srem('users', username)
    context.redis.srem('teams', username)
    context.redis.srem('admins', username)


def update_user(username, password=None, name=None, team=None, admin=None):
    user = Dict(get_user(username, include_password=True))
    if password:
        user.password = hash_password(password)
    if name:
        user.name = name
    if team:
        # gotta remove them from whatever team they're on first
        if user.team is not None:
            remove_user_from_team(user.username, user.team)
        add_user_to_team(user.username, team)
    if admin == 'A' or admin is True or admin is False:
        user.admin = admin

    context.redis.set(username, pickle.dumps(user.to_dict()))

# delete_user('tester')
# create_new_user('tester', 'test', name='Testy McTesterson', admin=True)
# create_new_user('arnohld@thegovernator.com', 'test', name='The Schwartzmeister', admin=False)
# create_new_user('thefunnyone@topgear.co.uk', 'test', name='James May', admin=False)
# create_new_user('knockknockwhosthere@thedoctor.com', 'test', name='Doctor Who', admin=True)
# create_new_user('notch@minecraft.net', 'test', name='Markus Persson', admin=True)
# update_user('notch@minecraft.net', name="Markus Persson")



# *****************************************
#   _______ ______          __  __  _____
#  |__   __|  ____|   /\   |  \/  |/ ____|
#     | |  | |__     /  \  | \  / | (___
#     | |  |  __|   / /\ \ | |\/| |\___ \
#     | |  | |____ / ____ \| |  | |____) |
#     |_|  |______/_/    \_\_|  |_|_____/
# *****************************************

# Team structure: pickled dict
# title --> str
# members --> list of str
# description --> str
# leader --> str (username)


def is_valid_team(team):
    return team in context.redis.smembers('teams')


def get_list_of_teams():
    # if I do this in prod, shoot me
    # grabs a set from redis, converts it from bytes to strings, then trims
    # each entry to make it look right
    return [x[2:-1] for x in list(map(str, context.redis.smembers('teams')))]


def get_users_not_assigned_to_teams():
    users = context.redis.smembers('users')
    teams = context.redis.smembers('teams')
    teammates = []
    for team in teams:
        teammates.append(context.redis.smembers(team))
    return [x for x in users if x not in teammates]


def get_team(team):
    team = context.redis.get(team)
    if team:
        return pickle.loads(team)
    return None


def add_team(team):
    newteam = Dict()
    newteam.title = team
    newteam.members = []
    newteam.description = None
    newteam.leader = None

    result = context.redis.sadd('teams', team)
    if int(result) == 1:
        context.redis.set(team, pickle.dumps(newteam.to_dict()))
        return True
    return False


def delete_team(team):
    team_obj = get_team(team)
    if not team_obj:
        return False
    users = get_team(team)['members']
    for user in users:
        user = get_user(user)
        update_user(user['username'], team=None)
    context.redis.delete(team)
    context.redis.srem('teams', team)
    return True


def add_user_to_team(username, team):
    team_obj = get_team(team)
    if team_obj is None:
        return
    if not team_obj.get('members', None):
        team_obj['members'] = []
        team_obj['members'] = team_obj['members'].append(username)
    context.redis.set(team, pickle.dumps(team_obj))


def remove_user_from_team(username, team):
    team_obj = get_team(team)
    if not team_obj.get('members', None):
        return
    team_obj['members'] = team_obj['members'].pop(username)
    context.redis.set(team, pickle.dumps(team_obj))


def get_team_of_user(username):
    teams = context.redis.smembers('teams')
    for team in teams:
        if username in get_team(team)['members']:
            return team

# add_team('Gryffindor')
# add_team('Ravenclaw')
# add_team('Hufflepuff')
# add_team('Slytherin')
# add_user_to_team('arnohld@thegovernator.com', 'Gryffindor')
# add_user_to_team('knockknockwhosthere@thedoctor.com', 'Gryffindor')
# add_user_to_team('notch@minecraft.net', 'Ravenclaw')
# *********************************************
#   ________      ________ _   _ _______ _____
#  |  ____\ \    / /  ____| \ | |__   __/ ____|
#  | |__   \ \  / /| |__  |  \| |  | | | (___
#  |  __|   \ \/ / |  __| | . ` |  | |  \___ \
#  | |____   \  /  | |____| |\  |  | |  ____) |
#  |______|   \/   |______|_| \_|  |_| |_____/
# *********************************************

# An event is a pickled dict, just like the others. Starting to see a theme here?
#
# Title: str
# start_date: int, unix timestamp
# end_date: int, unix timestamp
# categories: list, with each entry being a dict of name and weight
#   [{'name': 'category1', 'weight':3}, {'name': 'category2', 'weight':1}]

def add_event(name, start_date=None, end_date=None, categories=None):
    event = Dict()
    event.title = name
    event.start_date = start_date
    event.end_date = end_date
    event.categories = categories

    return True if context.redis.set('event::' + name, pickle.dumps(event.to_dict())) == 1 else False


def delete_event(name):
    name = 'event::' + name
    result = context.redis.get(name)
    if result:
        context.redis.delete(name)
        return True
    else:
        return False


def edit_event(name, new_name=None, start_date=None, end_date=None, categories=None):
    event = context.redis.get('event::' + name)
    if not event:
        return False

    event = Dict(pickle.loads(event))
    if new_name:
        event.title = new_name
        name = new_name
    if start_date:
        event.start_date = start_date
    if end_date:
        event.end_date = end_date
    if categories:
        event.categories = categories

    return True if context.redis.set('event::' + name, pickle.dumps(event.to_dict())) == 1 else False


def get_event(name):
    result = context.redis.get('event::' + name)
    if result:
        return pickle.loads(result)
    return None
