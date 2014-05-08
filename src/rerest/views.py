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
from bson import ObjectId
from bson.errors import InvalidId
from flask import current_app, jsonify, json, request, g

from flask.views import MethodView

from rerest import mq
from rerest.decorators import (
    remote_user_required, require_database, inject_request_id, check_group)
from rerest.validators import validate_playbook


class V0DeploymentAPI(MethodView):

    methods = ['POST']
    #: Decorators to be applied to all API methods in this class.
    decorators = [remote_user_required, check_group, inject_request_id]

    def put(self, project):
        """
        Creates a new deployment.
        """
        try:
            current_app.logger.info(
                'Starting release for %s as %s for user %s' % (
                    project, request.request_id, request.remote_user))
            mq_data = current_app.config['MQ']
            jc = mq.JobCreator(
                server=mq_data['SERVER'],
                port=int(mq_data['PORT']),
                user=mq_data['USER'],
                password=mq_data['PASSWORD'],
                vhost=mq_data['VHOST'],
                logger=current_app.logger,
                request_id=request.request_id
            )
            current_app.logger.info('Creating job for project %s' % project)
            #                      Here we are passing json if there is any
            #                      or returning None otherwise (silent=True)
            try:
                dynamic = json.loads(request.data)
                # If we got nothing then raise (to catch)
                if dynamic is None:
                    raise ValueError('No data')
            except ValueError:
                current_app.logger.debug('No data sent in request for dynamic'
                                         'variables.')
                dynamic = {}
            current_app.logger.info(
                "Received dynamic keys: %s" % (
                    str(dynamic)))
            jc.create_job(project, dynamic=dynamic)
            confirmation_id = jc.get_confirmation(project)
            current_app.logger.debug(
                'Confirmation id received for request id %s' % (
                    request.request_id))
            if confirmation_id is None:
                current_app.logger.debug(
                    'Confirmation for %s was None meaning the '
                    'project does not exist. request id %s' % (
                        project, request.request_id))
                current_app.logger.info(
                    'Bus could not find project for request id %s' % (
                        request.request_id))
                return jsonify({
                    'status': 'error',
                    'message': 'project not found'}), 404

            current_app.logger.debug(
                'Confirmation for %s is %s. request id %s' % (
                    project, confirmation_id, request.request_id))
            current_app.logger.info(
                'Created release as %s for request id %s' % (
                    confirmation_id, request.request_id))
            return jsonify({'status': 'created', 'id': confirmation_id}), 201
        except KeyError, kex:
            current_app.logger.error(
                'Error creating job for %s. Missing '
                'something in the MQ config section? %s: %s. '
                'Request id: %s' % (
                    project, type(kex).__name__, kex, request.request_id))
        except Exception, ex:
            # As there is a lot of other possible network related exceptions
            # this catch all seems to make sense.
            current_app.logger.error(
                'Error creating job for %s. %s: %s. '
                'Request id: %s' % (
                    project, type(ex).__name__, ex, request.request_id))
            return jsonify({
                'status': 'error', 'message': 'unknown error'}), 500


class V0PlaybookAPI(MethodView):

    methods = ['GET', 'PUT', 'POST', 'DELETE']
    #: Decorators to be applied to all API methods in this class.
    decorators = [
        remote_user_required, check_group, require_database, inject_request_id]

    def get(self, project=None, id=None):
        """
        Gets a list or single playbook and returns it to the requestor.
        """

        if id is None:
            # List playbooks
            current_app.logger.debug(
                'User %s is listing known playbooks for project %s. '
                'Request id: %s' % (
                    request.remote_user, project, request.request_id))

            if project is None:
                playbooks = g.db.re.playbooks.find()
            else:
                playbooks = g.db.re.playbooks.find({"project": str(project)})
            items = []
            for item in playbooks:
                item["id"] = str(item["_id"])
                del item["_id"]
                items.append(item)
            return jsonify({'status': 'ok', 'items': items}), 200

        # One playbook
        playbook = g.db.re.playbooks.find_one({
            "_id": ObjectId(id), "project": str(project)})

        if playbook is None:
            return jsonify({'status': 'not found'}), 404
        current_app.logger.debug(
            'Listing known playbook %s for project %s. '
            'Request id: %s' % (
                id, project, request.request_id))

        playbook["id"] = str(playbook["_id"])
        del playbook["_id"]
        return jsonify({'status': 'ok', 'item': playbook}), 200

    def put(self, project):
        """
        Creates a new playbook for a project.
        """
        current_app.logger.info(
            'Creating a new playbook for project %s by user %s. '
            'Request id: %s' % (
                project, request.remote_user, request.request_id))

        playbook = json.loads(request.data)
        try:
            validate_playbook(playbook)
            playbook["project"] = str(project)
            id = g.db.re.playbooks.insert(playbook)

            return jsonify({'status': 'created', 'id': str(id)}), 201
        except KeyError, ke:
            return jsonify({'status': 'bad request', 'message': str(ke)}), 400

    def post(self, project, id):
        """
        Replaces a playbook for a project.
        """
        current_app.logger.info(
            'Updating a playbook for project %s by user %s. '
            'Request id: %s' % (
                project, request.remote_user, request.request_id))
        try:
            oid = ObjectId(id)
        except InvalidId:
            return jsonify({'status': 'bad request', 'message': 'Bad id'}), 400

        exists = g.db.re.playbooks.find_one({"_id": oid})
        if exists:
            playbook = json.loads(request.data)
            playbook["project"] = str(project)
            try:
                validate_playbook(playbook)
                g.db.re.playbooks.update({"_id": oid}, playbook)
                return jsonify({'status': 'ok', 'id': str(exists['_id'])}), 200
            except KeyError, ke:
                return jsonify({
                    'status': 'bad request', 'message': str(ke)}), 400

        return jsonify({'status': 'not found'}), 404

    def delete(self, project, id):
        """
        Deletes a playbook.
        """

        try:
            oid = ObjectId(id)
        except InvalidId:
            return jsonify({'status': 'bad request', 'message': 'Bad id'}), 400

        current_app.logger.info(
            'Deleting playbook %s for project %s by user %s. '
            'Request id: %s' % (
                id, project, request.remote_user, request.request_id))
        exists = g.db.re.playbooks.find_one({"_id": oid})
        if exists:
            g.db.re.playbooks.remove({"_id": oid})
            return jsonify({'status': 'gone'}), 410
        return jsonify({'status': 'not found'}), 404


def make_routes(app):
    """
    Makes and appends routes to app.
    """
    deployment_api_view = V0DeploymentAPI.as_view('deployment_api_view')
    playbook_api_view = V0PlaybookAPI.as_view('playbook_api_view')

    app.add_url_rule('/api/v0/<project>/deployment/',
                     view_func=deployment_api_view, methods=['PUT', ])

    app.add_url_rule('/api/v0/playbooks/',
                     view_func=playbook_api_view, methods=[
                         'GET'])

    app.add_url_rule('/api/v0/<project>/playbook/',
                     view_func=playbook_api_view, methods=[
                         'GET', 'PUT'])
    app.add_url_rule('/api/v0/<project>/playbook/<id>/',
                     view_func=playbook_api_view, methods=[
                         'GET', 'POST', 'DELETE'])

    app.logger.info('Added v0 routes.')
