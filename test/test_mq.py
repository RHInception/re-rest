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

import logging
import mock
import pika

from flask import json

from rerest import mq

from . import TestCase, unittest

mq.pika = mock.Mock(pika)


class TestJobCreator(TestCase):

    def tearDown(self):
        """
        Reset the mock.
        """
        mq.pika.BlockingConnection.reset_mock()

    def test_create_object(self):
        """
        Test JobCreator is created as expected.
        """
        jc = mq.JobCreator(
            'server', 5672, 'user', 'pass', 'vhost', logging.getLogger())
        print mq.pika.BlockingConnection.call_count
        assert mq.pika.BlockingConnection.call_count == 1
        assert jc._channel.queue_declare.call_count == 1
        jc._channel.queue_declare.assert_called_with(auto_delete=True)

    def test_create_job(self):
        """
        Test start_job.
        """
        jc = mq.JobCreator(
            'server', 5672, 'user', 'pass', 'vhost', logging.getLogger())
        assert jc.create_job('project') is None  # No return value
        assert jc._channel.basic_publish.call_count == 1
        assert jc._channel.basic_publish.call_args[0][0] == 're'
        assert jc._channel.basic_publish.call_args[0][1] == 'job.create'
        assert jc._channel.basic_publish.call_args[0][2] == (
            '{"project": "project"}')

    def test_get_confirmation(self):
        """
        Test confirmation response.
        """
        #FIXME: Some mocks are hanging around messing with the results here
        #       Fix soon.
        jc = mq.JobCreator(
            'server', 5672, 'user', 'pass', 'vhost', logging.getLogger())
        jc.create_job('project')
        jc._channel.consume = mock.MagicMock()
        # Perfect world scenario
        jc._channel.consume.return_value = [[
            mock.Mock(delivery_tag=1),
            mock.Mock(delivery_tag=1),
            '{"id": 1}']]
        assert jc.get_confirmation() == 1
        '''
        # Not so perfect world scenario
        jc._channel.consume.return_value = [[
            mock.Mock(delivery_tag=1),
            mock.Mock(delivery_tag=1),
            'not json data so it will error']]
        self.assertRaises(Exception, jc.get_confirmation)
        '''
