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


def start_job():
    """
    Starts a job via the mq.
    """
    connection = pika.BlockingConnection()
    channel = connection.channel()
    # tmp_q is the queue which we will listen on for a response
    tmp_q = channel.queue_declare(auto_delete=True)
    # Set up the reply-to to our temporary queue
    properties = pika.spec.BasicProperties()
    properties.reply_to = tmp_q.method.queue
    # Send the message
    channel.basic_publish(
        'releaseengine', 'job.create',
        json.dumps({'some': 'info'}), properties=properties)

    for method_frame, header_frame, body in channel.consume(
            tmp_q.method.queue, exclusive=True):
        try:
            job_id = json.loads(body)['id']
            channel.basic_ack(method_frame.delivery_tag)
            return job_id
        except Exception, ex:
            channel.basic_reject(method_frame.delivery_tag)
            raise ex
        finally:
            channel.close()
