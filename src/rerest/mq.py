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
Message queue helpers.
"""

import pika

from flask import json


class JobCreator(object):

    def __init__(self):
        connection = pika.BlockingConnection()
        self._channel = connection.channel()
        # tmp_q is the queue which we will listen on for a response
        self._tmp_q = self._channel.queue_declare(auto_delete=True)

    def create_job(self, exchange='re', topic='job.create'):
        # Set up the reply-to to our temporary queue
        properties = pika.spec.BasicProperties()
        properties.reply_to = self._tmp_q.method.queue
        # Send the message
        self._channel.basic_publish(
            exchange, topic,
            json.dumps({'some': 'info'}), properties=properties)

    def get_confirmation(self):
        for method_frame, header_frame, body in self._channel.consume(
                self._tmp_q.method.queue, exclusive=True):
            try:
                job_id = json.loads(body)['id']
                self._channel.basic_ack(method_frame.delivery_tag)
                return job_id
            except Exception, ex:
                self._channel.basic_reject(method_frame.delivery_tag)
                raise ex
            finally:
                self._channel.close()
