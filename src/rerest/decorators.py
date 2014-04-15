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

from flask import request, jsonify


def remote_user_required(f):
    """
    Ensures a user has authenticated with the proxy.
    """
    def decorator(*args, **kwargs):
        if not request.remote_user:
            return jsonify({'status': 'error', 'message': 'unauthorized'}), 401
        return f(*args, **kwargs)
    return decorator
