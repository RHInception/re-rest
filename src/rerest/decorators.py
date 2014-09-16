# Copyright (C) 2014 SEE AUTHORS FILE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Decorators.
"""
import uuid
import urllib

from flask import current_app, request, jsonify, g


def remote_user_required(f):
    """
    Ensures a user has authenticated with the proxy.
    """

    def decorator(*args, **kwargs):
        if not request.remote_user:
            return jsonify({'status': 'error', 'message': 'unauthorized'}), 401
        return f(*args, **kwargs)
    return decorator


def check_group(f):
    """
    Ensures a user is part of a required group. Needs remote_user_required!
    """

    def decorator(*args, **kwargs):
        # Load the callable
        mod, meth = current_app.config['AUTHORIZATION_CALLABLE'].split(':')
        check_auth = getattr(__import__(mod, fromlist=['True']), meth)

        if check_auth(request.remote_user, request.view_args)[0]:
            current_app.logger.debug(
                'User %s successfully authenticated for %s' % (
                    request.remote_user, request.path))
            return f(*args, **kwargs)
        current_app.logger.warn(
            'User %s failed authentication for %s' % (
                request.remote_user, request.path))
        return jsonify({'status': 'error', 'message': 'forbidden'}), 403
    return decorator


def check_environment_and_group(f):
    """
    Ensure a user has the proper permission to access a group
    and play in an environment
    """

    def decorator(*args, **kwargs):
        # First check access to the requested group
        mod, meth = current_app.config['AUTHORIZATION_CALLABLE'].split(':')
        check_auth = getattr(__import__(mod, fromlist=['True']), meth)

        auth_check = check_auth(request.remote_user, request.view_args)
        if auth_check[0]:
            current_app.logger.debug(
                'User %s successfully authenticated for %s' % (
                    request.remote_user, request.path))

            # Now check for environment permissions
            emod, emeth = current_app.config[
                'AUTHORIZATION_ENVIRONMENT_CALLABLE'].split(':')
            check_env_auth = getattr(
                __import__(emod, fromlist=['True']), emeth)

            if check_env_auth(
                    request.remote_user, request.view_args.get('id', None),
                    auth_check[1]):
                current_app.logger.debug(
                    'User %s has access to all hosts listed in %s' % (
                        request.remote_user, request.view_args['id']))
                return f(*args, **kwargs)

            current_app.logger.warn(
                'User %s does not have permission to all hosts in %s' % (
                    request.remote_user, request.view_args['id']))
            return jsonify({
                'status': 'error',
                'message': ('Your user does not have access to all the '
                            'hosts in the given playbook.')}), 403
        current_app.logger.warn(
            'User %s failed authentication for %s' % (
                request.remote_user, request.path))
        return jsonify({'status': 'error', 'message': 'forbidden'}), 403
    return decorator


def inject_request_id(f):
    """
    Injects a request_id into the view.
    """
    def decorator(*args, **kwargs):
        request.request_id = str(uuid.uuid4())
        return f(*args, **kwargs)
    return decorator


def require_database(f):
    """
    Ensures that g.db is set and connected.
    """

    def decorator(*args, **kwargs):
        db = getattr(g, 'db', None)
        if db:
            # TODO: check staleness
            pass
        else:
            import pymongo
            mongo_cfg = current_app.config['MONGODB_SETTINGS']
            g.db = pymongo.MongoClient(
                'mongodb://%s:%s@%s:%s/%s' % (
                    urllib.quote(mongo_cfg['USERNAME']),
                    urllib.quote(mongo_cfg['PASSWORD']),
                    mongo_cfg['HOST'],
                    int(mongo_cfg['PORT']),
                    mongo_cfg['DB']))
        return f(*args, **kwargs)
    return decorator
