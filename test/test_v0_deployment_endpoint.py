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

import pika
import mock

from flask import request, json

from . import TestCase, unittest

from contextlib import nested

from rerest import mq
from rerest.mq import JobCreator

# Mock stuff
mq.pika = mock.Mock(pika)
orig_jc = JobCreator


class TestV0DeploymentEndpoint(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        mq.JobCreator.get_confirmation = mock.MagicMock(
            mq.JobCreator.get_confirmation, return_value=1)

    def tearDown(self):
        mq.jobCreator = orig_jc

    def test_create_new_deployment_with_user(self):
        """
        Test creating new deployment requests.
        """
        # Check with good input
        with mock.patch('pymongo.MongoClient') as mc:
            mc.db.re.playbooks.find.return_value = [{
                'execution': [{'hosts': ['host123']}]}]

            with self.test_client() as c:
                response = c.put(
                    '/api/v0/test/playbook/5408c8b002b67c0013ac3737/deployment/',
                    environ_overrides={'REMOTE_USER': 'testuser'})
                assert request.view_args['group'] == 'test'
                assert request.view_args['id'] == '5408c8b002b67c0013ac3737'
                assert response.status_code == 201
                assert response.mimetype == 'application/json'
                result = json.loads(response.data)
                assert result['status'] == 'created'
                assert result['id'] == 1

            # Check with bad input
            with self.test_client() as c:
                response = c.post('/api/v0//deployment/')
                assert response.status_code == 404

    def test_create_new_deployment_without_user(self):
        """
        New deployments should fail without a user.
        """
        with mock.patch('pymongo.MongoClient') as mc:
            mc.db.re.playbooks.find.return_value = [{
                'execution': [{'hosts': ['host123']}]}]

            # Check with good input
            with self.test_client() as c:
                response = c.put(
                    '/api/v0/test/playbook/5408c8b002b67c0013ac3737/deployment/')
                assert request.view_args['group'] == 'test'
                assert request.view_args['id'] == '5408c8b002b67c0013ac3737'
                assert response.status_code == 401
                assert response.mimetype == 'application/json'
                result = json.loads(response.data)
                assert result['status'] == 'error'
                assert result['message'] == 'unauthorized'
