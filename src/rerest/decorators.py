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
Authentication decorators.
"""

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


def require_database(f):
    """
    Ensures that g.db is set and connected.
    """

    def decorator(*args, **kwargs):
        db = g.get('db', None)
        print db, "***"
        if db:
            # TODO: check staleness
            pass
        else:
            import pymongo
            mongo_cfg = current_app.config['MONGODB_SETTINGS']
            g.db = pymongo.MongoClient(
                'mongodb://%s:%s@%s:%s/%s' % (
                    mongo_cfg['USERNAME'],
                    mongo_cfg['PASSWORD'],
                    mongo_cfg['HOST'],
                    int(mongo_cfg['PORT']),
                    mongo_cfg['DB']))
        return f(*args, **kwargs)
    return decorator
