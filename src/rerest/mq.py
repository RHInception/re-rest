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

    def __init__(self, server, port, user, password, vhost, logger):
        self.logger = logger
        creds = pika.PlainCredentials(user, password)

        # TODO: add ssl=True
        params = pika.ConnectionParameters(
            server,
            port,
            vhost,
            creds,
        )

        self.logger.debug('Attemtping connection with amqp://%s:%s@%s:%s%s' % (
            user, password, server, port, vhost))
        connection = pika.BlockingConnection(params)
        self.logger.info('Connected to amqp://%s:***@%s:%s%s' % (
            user, server, port, vhost))
        self._channel = connection.channel()
        # tmp_q is the queue which we will listen on for a response
        self._tmp_q = self._channel.queue_declare(auto_delete=True)

    def create_job(self, project, exchange='re', topic='job.create'):
        # Set up the reply-to to our temporary queue
        properties = pika.spec.BasicProperties()
        properties.reply_to = self._tmp_q.method.queue

        self.logger.info('Creating a job for project %s using exchange '
                         '%s and topic %s. Temp queue name is %s' % (
                         project, exchange, topic, self._tmp_q.method.queue))

        # Send the message
        self._channel.basic_publish(
            exchange, topic,
            json.dumps({'project': project}), properties=properties)

        self.logger.debug('Job request sent for project %s using exchange '
                          '%s and topic %s' % (project, exchange, topic))

    def get_confirmation(self):
        self.logger.info('Listening for response on temp queue %s' % (
            self._tmp_q.method.queue))
        for method_frame, header_frame, body in self._channel.consume(
                self._tmp_q.method.queue):
            try:
                job_id = json.loads(body)['id']
                self._channel.basic_ack(method_frame.delivery_tag)
                self.logger.debug('Got job id of %s' % job_id)
                return job_id
            except Exception, ex:
                self._channel.basic_reject(method_frame.delivery_tag)
                self.logger.error('Error received: %s: %s' % (type(ex), ex))
                raise ex
            finally:
                self.logger.debug('Closed bus connection.')
                self._channel.close()
