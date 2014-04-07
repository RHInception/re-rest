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
Views.
"""

from flask import jsonify

from flask.views import MethodView

from rerest import mq


class V0DeploymentAPI(MethodView):

    methods = ['POST']

    def put(self, project):
        """
        Creates a new deployment.
        """
        try:
            jc = mq.JobCreator()
            jc.create_job()
            confirmation_id = jc.get_confirmation()
            return jsonify({'status': 'created', 'id': confirmation_id}), 201
        except Exception, ex:
            # TODO: logging
            print type(ex), ex
            return jsonify({'status': 'error'}), 500


def make_routes(app):
    """
    Makes and appends routes to app.
    """
    deployment_api_view = V0DeploymentAPI.as_view('deployment_api_view')
    app.add_url_rule('/api/v0/<project>/deployment/',
                     view_func=deployment_api_view, methods=['PUT', ])
