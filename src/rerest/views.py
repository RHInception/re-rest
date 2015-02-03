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
from flask import (
    current_app, jsonify, json, request, g, Response, render_template)
from datetime import datetime as dt

from flask.views import MethodView

from rerest import mq, serialize
from rerest.contextfilter import ContextFilter
from rerest.decorators import (
    remote_user_required, require_database, inject_request_id,
    check_group, check_environment_and_group)
from rerest.validators import validate_playbook, ValidationError
from jinja2 import TemplateNotFound

import yaml


class V0StatusAPI(MethodView):
    """Inspect the status of a deployment"""

    methods = ['GET']

    #: Decorators to be applied to all API methods in this class.
    decorators = [
        remote_user_required,
        inject_request_id,
        require_database
    ]

    def get(self, dpid):
        """Get the status of a deployment with a state id of ``dpid``."""
        filter = {
            '_id': ObjectId(str(dpid))
        }
        # Limit fields returned just to:
        projection = {
            "created": 1,
            "ended": 1,
            "failed": 1,
            "active_step": 1,
            "failed_step": 1,
            '_id': 0
        }
        record = g.db.re.state.find_one(
            filter,
            projection
        )

        ContextFilter.set_field('deployment_id', str(dpid))

        if record is None:
            # 404: "no such deployment" - the deployment requested does not exist
            response = {
                "status": "not found",
                "deployment": dpid
            }
            status_code = 404
            current_app.logger.info("Deployment status: Not found")
        else:
            # 200: "completed" - the deployment requested exists and
            # finished successfully failed = False AND ended is not
            # None
            if ((record['failed'] is not None) and
                    (record['failed'] is not True) and
                    (record['ended'] is not None)):
                duration = record['ended'] - record['created']
                response = {
                    "created": record['created'],
                    "deployment": dpid,
                    "duration": int(duration.total_seconds()),
                    "ended": record['ended'],
                    "status": "completed",
                }
                status_code = 200
                current_app.logger.info("Deployment status: Completed without error")

            # 202: "currently running step frob:Nicate" - the
            # deployment requested exists, but is still being
            # processed ended is not None
            elif record['ended'] is None:
                duration = dt.utcnow() - record['created']
                response = {
                    "active_step": record['active_step'],
                    "created": record['created'],
                    "deployment": dpid,
                    "duration": int(duration.total_seconds()),
                    "status": "in progress",
                }
                status_code = 202
                current_app.logger.info("Deployment status: In progress")

            # 400: "failed" - the deployment requested exists but
            # finished with errors
            elif ((record['failed'] is True) and
                  (record['ended'] is not None)):
                duration = record['ended'] - record['created']
                response = {
                    "created": record['created'],
                    "deployment": dpid,
                    "duration": int(duration.total_seconds()),
                    "ended": record['ended'],
                    "failed_step": record['failed_step'],
                    "status": "failed",
                }
                status_code = 400
                current_app.logger.info("Deployment status: Failed")

        return jsonify(response), status_code


class V0DeploymentAPI(MethodView):

    methods = ['PUT']
    #: Decorators to be applied to all API methods in this class.
    decorators = [
        remote_user_required, check_environment_and_group,
        inject_request_id, require_database]

    def put(self, group, id):
        """
        Creates a new deployment.
        """
        try:
            ContextFilter.set_field('user_id', request.remote_user)
            ContextFilter.set_field('source_ip', request.remote_addr)
            current_app.logger.info(
                'Starting release for %s as %s for user %s' % (
                    group, request.request_id, request.remote_user))
            mq_data = current_app.config['MQ']
            jc = mq.JobCreator(
                mq_data,
                logger=current_app.logger,
                request_id=request.request_id
            )
            ContextFilter.set_field('playbook_id', id)
            current_app.logger.info(
                'Creating job for group %s, playbook %s' % (
                    group, id))
            try:
                dynamic = json.loads(request.data)
                # If we got nothing then raise (to catch)
                if dynamic is None:
                    raise ValueError('No data')
            except ValueError:
                current_app.logger.info(
                    'No data sent in request for dynamic variables.')
                dynamic = {}
            current_app.logger.info(
                "Received dynamic keys: %s" % (
                    str(dynamic)))
            jc.create_job(group, id, dynamic=dynamic)
            confirmation_id = jc.get_confirmation(group)
            current_app.logger.debug(
                'Confirmation id received for request id %s' % (
                    request.request_id))
            if confirmation_id is None:
                current_app.logger.debug(
                    'Confirmation for %s was None meaning the '
                    'group does not exist. request id %s' % (
                        group, request.request_id))
                current_app.logger.info(
                    'Bus could not find group for request id %s' % (
                        request.request_id))
                return jsonify({
                    'status': 'error',
                    'message': 'group not found'}), 404

            current_app.logger.debug(
                'Confirmation for %s/%s is %s. request id %s' % (
                    group, id, confirmation_id, request.request_id))
            current_app.logger.info(
                'Created release as %s for request id %s' % (
                    confirmation_id, request.request_id))
            return jsonify({'status': 'created', 'id': confirmation_id}), 201
        except KeyError, kex:
            current_app.logger.error(
                'Error creating job for %s/%s. Missing '
                'something in the MQ config section? %s: %s. '
                'Request id: %s' % (
                    group, id, type(kex).__name__, kex, request.request_id))
        except Exception, ex:
            # As there is a lot of other possible network related exceptions
            # this catch all seems to make sense.
            current_app.logger.error(
                'Error creating job for %s/%s. %s: %s. '
                'Request id: %s' % (
                    group, id, type(ex).__name__, ex, request.request_id))
            return jsonify({
                'status': 'error', 'message': 'unknown error'}), 500


class V0PlaybookAPI(MethodView):

    methods = ['GET', 'PUT', 'POST', 'DELETE']
    #: Decorators to be applied to all API methods in this class.
    decorators = [
        remote_user_required, check_group, require_database, inject_request_id]

    def get(self, group=None, id=None):
        """
        Gets a list or single playbook and returns it to the requestor.
        """
        # Serializer so we can handle json and yaml
        serializer = serialize.Serialize(request.args.get(
            'format', 'json'))

        if id is None:
            # List playbooks
            ContextFilter.set_field('user_id', request.remote_user)
            current_app.logger.info(
                'User %s is listing known playbooks for group %s. '
                'Request id: %s' % (
                    request.remote_user, group, request.request_id))

            # Sort by most recently added first
            if group is None:
                playbooks = g.db.re.playbooks.find().sort([('_id', -1)])
            else:
                playbooks = g.db.re.playbooks.find({"group": str(group)}).sort([('_id', -1)])
            items = []
            for item in playbooks:
                item["id"] = str(item["_id"])
                del item["_id"]
                items.append(item)
            # This must be a Response since it can be YAML or JSON.
            return Response(
                response=serializer.dump({'status': 'ok', 'items': items}),
                status=200,
                mimetype=serializer.mimetype)

        # One playbook
        playbook = g.db.re.playbooks.find_one({
            "_id": ObjectId(id), "group": str(group)})

        if playbook is None:
            return jsonify({'status': 'not found'}), 404
        current_app.logger.debug(
            'Listing known playbook %s for group %s. '
            'Request id: %s' % (
                id, group, request.request_id))

        del playbook["_id"]
        return Response(
            response=serializer.dump({'status': 'ok', 'item': playbook}),
            status=200,
            mimetype=serializer.mimetype)

    def put(self, group):
        """
        Creates a new playbook for a group.
        """
        # Serializer so we can handle json and yaml
        serializer = serialize.Serialize(request.args.get(
            'format', 'json'))

        ContextFilter.set_field('user_id', request.remote_user)
        # Gets the formatter info
        current_app.logger.info(
            'Creating a new playbook for group %s by user %s. '
            'Request id: %s' % (
                group, request.remote_user, request.request_id))

        try:
            playbook = serializer.load(request.data)
            validate_playbook(playbook)
            playbook["group"] = str(group)
            id = g.db.re.playbooks.insert(playbook)

            return jsonify({'status': 'created', 'id': str(id)}), 201
        except (KeyError, ValueError), ke:
            return jsonify(
                {'status': 'bad request', 'message': str(ke)}), 400
        except ValidationError:
            current_app.logger.error("The playbook does not conform to the spec")
            return jsonify({
                'status': 'bad request',
                'message': 'The playbook does not conform to the spec.'}), 400

    def post(self, group, id):
        """
        Replaces a playbook for a group.
        """
        # Serializer so we can handle json and yaml
        serializer = serialize.Serialize(request.args.get(
            'format', 'json'))

        ContextFilter.set_field('user_id', request.remote_user)
        current_app.logger.info(
            'Updating a playbook for group %s by user %s. '
            'Request id: %s' % (
                group, request.remote_user, request.request_id))
        try:
            oid = ObjectId(id)
        except InvalidId:
            return Response(
                response=serializer.dump(
                    {'status': 'bad request', 'message': 'Bad id'}),
                status=400,
                mimetype=serializer.mimetype)

        exists = g.db.re.playbooks.find_one({"_id": oid})
        if exists:
            try:
                playbook = serializer.load(request.data)
                playbook["group"] = str(group)
                validate_playbook(playbook)
                g.db.re.playbooks.update({"_id": oid}, playbook)
                return jsonify({
                    'status': 'ok', 'id': str(exists['_id'])}), 200
            except (KeyError, ValueError), ke:
                return jsonify({
                    'status': 'bad request', 'message': str(ke)}), 400
            except ValidationError:
                current_app.logger.error("The playbook does not conform to the spec")
                return jsonify({
                    'status': 'bad request',
                    'message': ('The playbook does not '
                                'conform to the spec.')}), 400

        return jsonify({'status': 'not found'}), 404

    def delete(self, group, id):
        """
        Deletes a playbook.
        """
        # NOTE: there is now format parameter since this doesn't accept or
        #       return a playbook.
        try:
            oid = ObjectId(id)
        except InvalidId:
            current_app.logger.error("The playbook ID given is invalid: %s" % str(id))
            return jsonify({'status': 'bad request', 'message': 'Bad id'}), 400

        ContextFilter.set_field('user_id', request.remote_user)
        current_app.logger.info(
            'Deleting playbook %s for group %s by user %s. '
            'Request id: %s' % (
                id, group, request.remote_user, request.request_id))
        exists = g.db.re.playbooks.find_one({"_id": oid})
        if exists:
            g.db.re.playbooks.remove({"_id": oid})
            return jsonify({'status': 'gone'}), 410
        return jsonify({'status': 'not found'}), 404


class V0GroupsAPI(MethodView):

    methods = ['GET']
    #: Decorators to be applied to all API methods in this class.
    decorators = [
        remote_user_required, require_database, inject_request_id]

    def get(self):
        """
        Gets a list of groups and returns it to the requestor.
        """
        # Serializer so we can handle json and yaml
        serializer = serialize.Serialize(request.args.get(
            'format', 'json'))

        # List playbooks
        ContextFilter.set_field('user_id', request.remote_user)
        current_app.logger.info(
            'User %s is listing known groups. Request id: %s' % (
                request.remote_user, request.request_id))

        groups = g.db.re.playbooks.distinct('group')
        items = []
        for group in groups:
            count = g.db.re.playbooks.find({'group': group}).count()
            items.append({'name': group, 'count': int(count)})
        # This must be a Response since it can be YAML or JSON.
        return Response(
            response=serializer.dump({'status': 'ok', 'items': items}),
            status=200,
            mimetype=serializer.mimetype)


# NOTE: The following are OFF by default and not considered ready for use
#       due to no unittesting.
class PlaybookIndex(MethodView):  # pragma: no cover

    methods = ['GET']
    #: Decorators to be applied to all API methods in this class.
    decorators = [
        remote_user_required, require_database, inject_request_id]

    def get(self, group=None, pbid=None):
        """new: return a directory index links to sub-directories holding
        playbooks. sorted by group.

        """
        return render_template(
            'playbookui_index.html',
            title="Playbook Index")


class PlaybookGroupIndex(MethodView):  # pragma: no cover

    methods = ['GET']
    #: Decorators to be applied to all API methods in this class.
    decorators = [
        remote_user_required, require_database, inject_request_id]

    def get(self, group):
        """return a directory index of playbooks for the given <group>
        """
        try:
            group = g.db.re.playbooks.find_one({'group': group})
            return render_template(
                'playbookui_layout.html',
                title="Playbooks",
                group=group['group'])
        except Exception, e:
            return Response(
                response="No groups found.",
                status=404)


def _decode_list(data):  # pragma: no cover
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv


def _decode_dict(data):  # pragma: no cover
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = _decode_dict(value)
        rv[key] = value
    return rv


# END untested code which is off by default ---


def make_routes(app):
    """
    Makes and appends routes to app.
    """
    deployment_api_view = V0DeploymentAPI.as_view('deployment_api_view')
    status_api_view = V0StatusAPI.as_view('status_api_view')
    groups_api_view = V0GroupsAPI.as_view('groups_api_view')
    playbook_api_view = V0PlaybookAPI.as_view('playbook_api_view')

    app.add_url_rule('/api/v0/deployment/status/<dpid>/',
                     view_func=status_api_view, methods=['GET'])

    app.add_url_rule('/api/v0/<group>/playbook/<id>/deployment/',
                     view_func=deployment_api_view, methods=['PUT', ])

    app.add_url_rule('/api/v0/groups/',
                     view_func=groups_api_view, methods=[
                         'GET'])

    app.add_url_rule('/api/v0/playbooks/',
                     view_func=playbook_api_view, methods=[
                         'GET'])

    app.add_url_rule('/api/v0/<group>/playbook/',
                     view_func=playbook_api_view, methods=[
                         'GET', 'PUT'])

    app.add_url_rule('/api/v0/<group>/playbook/<id>/',
                     view_func=playbook_api_view, methods=[
                         'GET', 'POST', 'DELETE'])

    ##################################################################
    # Views for the web index
    if app.config.get('PLAYBOOK_UI', False):
        playbook_index_view = PlaybookIndex.as_view('playbook_index')
        playbook_group_index_view = PlaybookGroupIndex.as_view(
            'playbook_group_index')

        app.add_url_rule('/',
                         view_func=playbook_index_view, methods=[
                             'GET'])

        app.add_url_rule('/<group>/',
                         view_func=playbook_group_index_view, methods=[
                             'GET'])

    app.logger.info('Added v0 routes.')
