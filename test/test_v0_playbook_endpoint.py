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
Unittests.
"""

import json
import mock
from bson import ObjectId
from flask import request, json, g

from . import TestCase, unittest

# Mock stuff
from rerest.app import app

from contextlib import contextmanager
from flask import appcontext_pushed


@contextmanager
def db_ctx(app):
    def handler(sender, **kwargs):
        g.db = mock.MagicMock()
        g.db.re.playbooks.insert.return_value = '53614ccf1370129d6f29c7dd'
        g.db.re.playbooks.save.return_value = '53614ccf1370129d6f29c7dd'
        g.db.re.playbooks.find_one.return_value = {
            "_id": ObjectId('53614ccf1370129d6f29c7dd'),
            "data": "test"}
        g.db.re.playbooks.remove.return_value = True

    with appcontext_pushed.connected_to(handler, app):
        yield


class TestV0PlaybookEndpoint(TestCase):

    def _check_unauth_response(self, response):
        assert request.view_args['project'] == 'test'
        assert response.status_code == 401
        assert response.mimetype == 'application/json'
        result = json.loads(response.data)
        assert result['status'] == 'error'
        assert result['message'] == 'unauthorized'
        # If everything passes return True
        return True

    def test_list_playbooks(self):
        """
        Test getting a list of playbooks.
        """
        with db_ctx(app):
            # Check with good input
            with self.test_client() as c:
                response = c.get(
                    '/api/v0/test/playbook/',
                    environ_overrides={'REMOTE_USER': 'testuser'})

                assert request.view_args['project'] == 'test'
                assert response.status_code == 200
                assert response.mimetype == 'application/json'
                result = json.loads(response.data)
                assert result['status'] == 'ok'
                assert type(result['items']) == list

            # Check with bad input
            with self.test_client() as c:
                response = c.get('/api/v0//playbook/')
                assert response.status_code == 404

            # If there is no user we should fail
            with self.test_client() as c:
                assert self._check_unauth_response(c.get(
                    '/api/v0/test/playbook/'))

    def test_get_a_single_playbook(self):
        """
        Test getting a single playbook.
        """

        with db_ctx(app):
            # Check with good input
            with self.test_client() as c:
                response = c.get(
                    '/api/v0/test/playbook/53614ccf1370129d6f29c7dd/',
                    environ_overrides={'REMOTE_USER': 'testuser'})

                assert request.view_args['project'] == 'test'
                assert request.view_args['id'] == '53614ccf1370129d6f29c7dd'
                assert response.status_code == 200
                assert response.mimetype == 'application/json'
                result = json.loads(response.data)
                assert result['status'] == 'ok'
                assert 'item' in result.keys()

            # Check with bad input
            with self.test_client() as c:
                response = c.get('/api/v0//playbook/')
                assert response.status_code == 404

            # If there is no user we should fail
            with self.test_client() as c:
                assert self._check_unauth_response(c.get(
                    '/api/v0/test/playbook/53614ccf1370129d6f29c7dd/'))

    def test_create_playbook(self):
        """
        Test creating a new playbook.
        """

        with db_ctx(app):
            # Check with good input
            with self.test_client() as c:
                response = c.put(
                    '/api/v0/test/playbook/',
                    data=json.dumps({'test': 'data'}),
                    environ_overrides={'REMOTE_USER': 'testuser'})

                assert request.view_args['project'] == 'test'
                assert response.status_code == 201
                assert response.mimetype == 'application/json'
                result = json.loads(response.data)
                assert result['status'] == 'created'
                assert result['id'] == '53614ccf1370129d6f29c7dd'

            # Check with bad input
            with self.test_client() as c:
                response = c.put('/api/v0//playbook/')
                assert response.status_code == 404

            # If there is no user we should fail
            with self.test_client() as c:
                assert self._check_unauth_response(c.put(
                    '/api/v0/test/playbook/'))

    def test_update_playbook(self):
        """
        Test updating a playbook.
        """
        with db_ctx(app):
            # Check with good input
            with self.test_client() as c:
                response = c.post(
                    '/api/v0/test/playbook/53614ccf1370129d6f29c7dd/',
                    data=json.dumps({'test': 'data'}),
                    environ_overrides={'REMOTE_USER': 'testuser'})

                assert request.view_args['project'] == 'test'
                assert response.status_code == 200
                assert response.mimetype == 'application/json'
                result = json.loads(response.data)
                assert result['status'] == 'ok'
                assert result['id'] == '53614ccf1370129d6f29c7dd'

            # Check with bad input
            with self.test_client() as c:
                response = c.post(
                    '/api/v0//playbook/53614ccf1370129d6f29c7dd/')
                assert response.status_code == 404

            with self.test_client() as c:
                response = c.post('/api/v0/test/playbook//')
                assert response.status_code == 404

            # If there is no user we should fail
            with self.test_client() as c:
                assert self._check_unauth_response(c.post(
                    '/api/v0/test/playbook/53614ccf1370129d6f29c7dd/'))

    def test_delete_playbook(self):
        """
        Test deleting a playbook with a user works.
        """
        with db_ctx(app):
            # Check with good input
            with self.test_client() as c:
                response = c.delete(
                    '/api/v0/test/playbook/53614ccf1370129d6f29c7dd/',
                    environ_overrides={'REMOTE_USER': 'testuser'})

                assert request.view_args['project'] == 'test'
                assert request.view_args['id'] == '53614ccf1370129d6f29c7dd'
                assert response.status_code == 410
                assert response.mimetype == 'application/json'
                result = json.loads(response.data)
                assert result['status'] == 'gone'

            # Check with bad input
            with self.test_client() as c:
                response = c.delete('/api/v0//playbook/')
                assert response.status_code == 404

            with self.test_client() as c:
                response = c.delete('/api/v0/test/playbook//')
                assert response.status_code == 404

            # If there is no user we should fail
            with self.test_client() as c:
                assert self._check_unauth_response(c.delete(
                    '/api/v0/test/playbook/53614ccf1370129d6f29c7dd/'))
