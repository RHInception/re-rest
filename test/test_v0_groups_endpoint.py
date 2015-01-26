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

import yaml
import mock

from bson import ObjectId
from flask import request, json, g, json

from . import TestCase, unittest

# Mock stuff
from rerest.app import app

from contextlib import contextmanager
from flask import appcontext_pushed



@contextmanager
def db_ctx(app):
    def handler(sender, **kwargs):
        g.db = mock.MagicMock()
        g.db.re.playbooks.distinct.return_value = ['group']

    with appcontext_pushed.connected_to(handler, app):
        yield


class TestV0GroupsEndpoint(TestCase):

    def _check_unauth_response(self, response):
        assert response.status_code == 401
        assert response.mimetype == 'application/json'
        result = json.loads(response.data)
        assert result['status'] == 'error'
        assert result['message'] == 'unauthorized'
        # If everything passes return True
        return True

    def test_list_groups(self):
        """
        Test getting a list of groups.
        """
        with db_ctx(app):
            # Check with good input
            with self.test_client() as c:
                response = c.get(
                    '/api/v0/groups/',
                    environ_overrides={'REMOTE_USER': 'testuser'})

                self.assertEquals(response.status_code, 200)
                self.assertEquals(response.mimetype, 'application/json')
                result = json.loads(response.data)
                self.assertEquals(result['status'], 'ok')
                assert type(result['items']) == list
                # When listing playbooks we should get ID's
                self.assertIn('name', result['items'][0].keys())
                self.assertIn('count', result['items'][0].keys())
                self.assertEquals('group', result['items'][0]['name'])

            # Check with bad input
            with self.test_client() as c:
                response = c.get('/api/v0//playbook/')
                assert response.status_code == 404
