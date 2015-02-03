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
import datetime

from . import TestCase, unittest

# Mock stuff
from rerest.app import app

from contextlib import contextmanager
from flask import appcontext_pushed


PLAYBOOK = {
    "group": "example group",
    "name": "my playbook",
    "execution": [{
        "description": "do stuff",
        "hosts": ["127.0.0.1"],
        "preflight": [
            "something:ToDo",
        ],
        "steps": [{
            "example:Step": {
                "command": "ls -l /"
            }
        }]}
    ]
}

UTCNOW = datetime.datetime.utcnow()
ONEDAY = datetime.timedelta(days=1)
YESTERDAY = UTCNOW - ONEDAY

@contextmanager
def db_ctx(app, status=None, dpid=None):
    def handler(sender, **kwargs):
        g.db = mock.MagicMock()
        if status is None:
            g.db.re.state.find_one.return_value = None
        # Completed
        elif status == 200:
            g.db.re.state.find_one.return_value = {
                "created": YESTERDAY,
                "failed": False,
                "ended": UTCNOW
            }
        # In progress
        elif status == 202:
            g.db.re.state.find_one.return_value = {
                "created": YESTERDAY,
                "failed": None,
                "ended": None,
                "active_step": "noop:UnitTest"
            }
        # deploy failed
        elif status == 400:
            g.db.re.state.find_one.return_value = {
                "created": YESTERDAY,
                "failed": True,
                "ended": UTCNOW,
                "failed_step": "noop:Fail"
            }

    with appcontext_pushed.connected_to(handler, app):
        yield


class TestV0StatusEndpoint(TestCase):
    #: Deployment ID
    dpid = "54cbec56feb9826e0a54feee"
    suffix = '/api/v0/deployment/status/'
    suffixd = suffix + str(dpid) + "/"

    def _check_unauth_response(self, response):
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.mimetype, 'application/json')
        result = json.loads(response.data)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['message'], 'unauthorized')
        # If everything passes return True
        return True

    def test_get_status_completed(self):
        """
        Status View: Gives back an OK (200) for finished deployments
        """
        with db_ctx(app, status=200, dpid=self.dpid):
            with self.test_client() as c:
                response = c.get(self.suffixd,
                                 environ_overrides={'REMOTE_USER': 'testuser'})
                self.assertEqual(response.status_code, 200)

    def test_get_status_in_progress(self):
        """
        Status View: Gives back an Accepted (202) for unfinished deployments
        """
        with db_ctx(app, status=202, dpid=self.dpid):
            with self.test_client() as c,\
                    mock.patch('rerest.views.dt') as views_dt:
                views_dt.utcnow.return_value = UTCNOW
                response = c.get(self.suffixd,
                                 environ_overrides={'REMOTE_USER': 'testuser'})
                body = json.loads(response.data)
                self.assertEqual(response.status_code, 202)
                self.assertEqual(body['duration'], ONEDAY.total_seconds())

    def test_get_status_failed(self):
        """
        Status View: Gives back a bad Request (400) for failed deployments
        """
        with db_ctx(app, status=400, dpid=self.dpid):
            with self.test_client() as c:
                response = c.get(self.suffixd,
                                 environ_overrides={'REMOTE_USER': 'testuser'})
                self.assertEqual(response.status_code, 400)

    def test_get_status_not_authorized(self):
        """
        Status View: Gives back an Unauthorized (401) for unauthenticated requests
        """
        with db_ctx(app):
            # If there is no user we should fail
            with self.test_client() as c:
                self.assertTrue(self._check_unauth_response(c.get(self.suffixd)))

    def test_get_status_not_found(self):
        """
        Status View: Gives back a Not Found (404) for missing playbooks
        """
        with db_ctx(app):
            with self.test_client() as c:
                response = c.get(self.suffix,
                                 environ_overrides={'REMOTE_USER': 'testuser'})
                self.assertEqual(response.status_code, 404)

            with self.test_client() as c:
                response = c.get(self.suffix + "29d6f29c7dd53614ccf13701/",
                                 environ_overrides={'REMOTE_USER': 'testuser'})
                self.assertEqual(response.status_code, 404)
