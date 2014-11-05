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
from rerest.mq import JobCreator as JC

from . import TestCase, unittest

mq.pika = mock.Mock(pika)
mq.pika.reset_mock()

MQ_CONFIG = {
    "SERVER": 'server',
    "PORT": 5672,
    "USER": 'user',
    "PASSWORD": 'pass',
    "VHOST": 'vhost'
}


class TestJobCreator(TestCase):

    def tearDown(self):
        """
        Reset the mock.
        """
        mq.pika.reset_mock()

    def test_create_object(self):
        """
        Test JobCreator is created as expected.
        """
        jc = mq.JobCreator(MQ_CONFIG, logging.getLogger(), 1)
        assert mq.pika.BlockingConnection.call_count == 1
        assert jc._channel.queue_declare.call_count == 1
        jc._channel.queue_declare.assert_called_with(auto_delete=True)

    def test_create_job(self):
        """
        Test start_job.
        """
        jc = mq.JobCreator(MQ_CONFIG, logging.getLogger(), 1)
        assert jc.create_job('group', '12345') is None  # No return value
        assert jc._channel.basic_publish.call_count == 1
        assert jc._channel.basic_publish.call_args[0][0] == 're'
        assert jc._channel.basic_publish.call_args[0][1] == 'job.create'
        assert json.loads(jc._channel.basic_publish.call_args[0][2]) == (
            {"playbook_id": "12345", "group": "group"})

    def test_get_confirmation(self):
        """
        Test confirmation response.
        """
        logger = mock.MagicMock()
        jc = mq.JobCreator(MQ_CONFIG, logger, 1)
        jc._channel.reset_mock()
        jc.create_job('group', '12345')

        # Perfect world scenario
        jc._channel.consume.return_value = [[
            mock.Mock(delivery_tag=1),
            mock.Mock(delivery_tag=1),
            '{"id": 10}']]

        logger.reset_mock()
        debug_count = logger.debug.call_count
        assert jc.get_confirmation('group') == 10
        assert logger.debug.call_count > debug_count

        logger.reset_mock()
        jc._channel.reset_mock()

        # Not so perfect world scenarios
        jc._channel.consume.return_value = [[
            mock.Mock(delivery_tag=1),
            mock.Mock(delivery_tag=1),
            'not json data so it will error']]

        jc.get_confirmation('group')
        assert jc._channel.basic_reject.call_count == 1
        assert logger.error.call_count == 1

        logger.reset_mock()
        jc._channel.reset_mock()

        jc._channel.basic_ack.side_effect = pika.exceptions.ChannelClosed
        jc.get_confirmation('group')
        assert logger.error.call_count == 1

        logger.reset_mock()
        jc._channel.reset_mock()

        jc._channel.basic_ack.side_effect = ValueError
        jc.get_confirmation('group')
        assert logger.error.call_count == 1
