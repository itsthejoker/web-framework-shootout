import binascii
import hashlib
import pickle

from voting.context import context

import cherrypy

class session(object):
    # I love small, reusable functions
    @staticmethod
    def is_authenticated(update_to=None):
        if update_to is not None:
            cherrypy.session['is_authenticated'] = update_to
        else:
            return cherrypy.session.get('is_authenticated', False)

    @staticmethod
    def get_username():
        # pull the username from the current session, otherwise try and pull it from the request
        result = cherrypy.session.get('username', None)
        print(result)
        return result if result else cherrypy.request.params.get('username', None)

    @staticmethod
    def get_password():
        # this one isn't saved, so we assume that it's in the request only.
        print(cherrypy.request.params.get('password', None))
        return cherrypy.request.params.get('password', None)

    @staticmethod
    def is_admin(update_to=None):
        if update_to is not None:
            cherrypy.session['is_admin'] = update_to
        else:
            return cherrypy.session['is_admin']

def hash_password(password):
    salt = context.redis.get('pass_the_salt')
    return binascii.hexlify(
        hashlib.pbkdf2_hmac('sha512', bytes(password.encode('utf-8')), salt, 100000)
    )

def validate_password(username, password):
    return (
        context.redis.sismember('users', username) is True and
        pickle.loads(context.redis.get(username))['password'] == hash_password(password)
    )

def validate_admin(username, password):
    return context.redis.sismember('admins', username) is True