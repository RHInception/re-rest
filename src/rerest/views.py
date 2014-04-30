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
import uuid

from flask import current_app, jsonify, request, g

from flask.views import MethodView

from rerest import mq
from rerest.decorators import remote_user_required, require_database


class V0DeploymentAPI(MethodView):

    methods = ['POST']
    #: Decorators to be applied to all API methods in this class.
    decorators = [remote_user_required]

    def put(self, project):
        """
        Creates a new deployment.
        """
        try:
            request_id = str(uuid.uuid4())

            user = request.environ.get('REMOTE_USER', 'ANONYMOUS')
            current_app.logger.info(
                'Starting release for %s as %s for user %s' % (
                    project, request_id, user))
            mq_data = current_app.config['MQ']
            jc = mq.JobCreator(
                server=mq_data['SERVER'],
                port=int(mq_data['PORT']),
                user=mq_data['USER'],
                password=mq_data['PASSWORD'],
                vhost=mq_data['VHOST'],
                logger=current_app.logger,
                request_id=request_id
            )
            current_app.logger.info('Creating job for project %s' % project)
            #                      Here we are passing json if there is any
            #                      or returning None otherwise (silent=True)
            try:
                dynamic = request.get_json(force=True, silent=True))
            except AttributeError:
                current_app.logger.debug('No data sent in request for dynamic'
                                         'variables.')
                dynamic = {}
            current_app.logger.info(
                "Received dynamic keys: %s" % (
                    str(dynamic)))
            jc.create_job(project, dynamic=dynamic)
            confirmation_id = jc.get_confirmation(project)
            current_app.logger.debug(
                'Confirmation id received for request id %s' % request_id)
            if confirmation_id is None:
                current_app.logger.debug(
                    'Confirmation for %s was None meaning the '
                    'project does not exist. request id %s' % (
                        project, request_id))
                current_app.logger.info(
                    'Bus could not find project for request id %s' % (
                        request_id))
                return jsonify({
                    'status': 'error',
                    'message': 'project not found'}), 404

            current_app.logger.debug(
                'Confirmation for %s is %s. request id %s' % (
                    project, confirmation_id, request_id))
            current_app.logger.info(
                'Created release as %s for request id %s' % (
                    confirmation_id, request_id))
            return jsonify({'status': 'created', 'id': confirmation_id}), 201
        except KeyError, kex:
            current_app.logger.error(
                'Error creating job for %s. Missing '
                'something in the MQ config section? %s: %s. '
                'Request id: %s' % (
                    project, type(kex).__name__, kex, request_id))
        except Exception, ex:
            # As there is a lot of other possible network related exceptions
            # this catch all seems to make sense.
            current_app.logger.error(
                'Error creating job for %s. %s: %s. '
                'Request id: %s' % (
                    project, type(ex).__name__, ex, request_id))
            return jsonify({
                'status': 'error', 'message': 'unknown error'}), 500


class V0PlaybookAPI(MethodView):

    methods = ['GET', 'PUT', 'POST', 'DELETE']
    #: Decorators to be applied to all API methods in this class.
    decorators = [remote_user_required, require_database]

    def get(self, project, id=None):
        request_id = str(uuid.uuid4())

        if id is None:
            # TODO: Get document from database
            current_app.logger.debug(
                'Listing known playbooks for project %s. '
                'Request id: %s' % (
                    project, request_id))
            return jsonify({'status': 'ok', 'items': [12345]}), 200

        # TODO: get documents from database
        current_app.logger.debug(
            'Listing known playbook %s for project %s. '
            'Request id: %s' % (
                id, project, request_id))
        return jsonify({'status': 'ok', 'item': {'data': 'here'}}), 200

    def put(self, project):
        request_id = str(uuid.uuid4())

        user = request.environ.get('REMOTE_USER', 'ANONYMOUS')
        current_app.logger.info(
            'Creating a new playbook for project %s by user %s. '
            'Request id: %s' % (
                project, request_id, user))
        # TODO: Insert into database
        return jsonify({'status': 'created', 'id': 2}), 201

    def post(self, project, id):
        request_id = str(uuid.uuid4())

        user = request.environ.get('REMOTE_USER', 'ANONYMOUS')
        current_app.logger.info(
            'Updating a playbook for project %s by user %s. '
            'Request id: %s' % (
                project, request_id, user))
        # TODO: Verify the record exists
        # TODO: Update record in the database
        return jsonify({'status': 'ok', 'id': 2}), 200

    def delete(self, project, id):
        request_id = str(uuid.uuid4())

        user = request.environ.get('REMOTE_USER', 'ANONYMOUS')
        current_app.logger.info(
            'Deleting playbook %s for project %s by user %s. '
            'Request id: %s' % (
                id, project, request_id, user))
        # TODO: Verify record exists
        # TODO: Delete record
        return jsonify({'status': 'gone'}), 410


def make_routes(app):
    """
    Makes and appends routes to app.
    """
    deployment_api_view = V0DeploymentAPI.as_view('deployment_api_view')
    playbook_api_view = V0PlaybookAPI.as_view('playbook_api_view')

    app.add_url_rule('/api/v0/<project>/deployment/',
                     view_func=deployment_api_view, methods=['PUT', ])

    app.add_url_rule('/api/v0/<project>/playbook/',
                     view_func=playbook_api_view, methods=[
                         'GET', 'PUT'])
    app.add_url_rule('/api/v0/<project>/playbook/<id>/',
                     view_func=playbook_api_view, methods=[
                         'GET', 'POST', 'DELETE'])

    app.logger.info('Added v0 routes.')
