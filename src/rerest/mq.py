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
import pika.exceptions

from flask import json


class JobCreator(object):
    """
    Handles creation of a release job.
    """

    def __init__(
            self, server, port, user, password,
            vhost, logger, request_id):
        """
        Creates a JobCreator instance.

        server is the MQ server name
        port is the MQ server port
        user is the MQ server user
        password is the MQ server password
        vhost is the MQ server vhost
        logger is the logger to output with
        request_id is the applications request identifier
        """
        self.logger = logger
        self.request_id = request_id
        creds = pika.PlainCredentials(user, password)

        # TODO: add ssl=True
        params = pika.ConnectionParameters(
            server,
            port,
            vhost,
            creds,
        )

        self.logger.debug(
            'Attemtping connection with amqp://%s:%s@%s:%s%s '
            'for Request id: %s' % (
                user, password, server, port, vhost, self.request_id))
        connection = pika.BlockingConnection(params)
        self.logger.info(
            'Connected to amqp://%s:***@%s:%s%s '
            'for request id %s' % (
                user, server, port, vhost, self.request_id))
        self._channel = connection.channel()
        self.logger.debug(
            'Declaring and binding queue for request id %s' % (
                self.request_id))
        # tmp_q is the queue which we will listen on for a response
        self._tmp_q = self._channel.queue_declare(auto_delete=True)
        self._channel.queue_bind(
            queue=self._tmp_q.method.queue, exchange='re',
            routing_key=self._tmp_q.method.queue)
        self.logger.info(
            'Queue bound with routing id %s '
            'for request id %s' % (
                self._tmp_q.method.queue, self.request_id))

    def create_job(
            self, project, dynamic=None, exchange='re', topic='job.create'):
        """
        Emits a message notifying the FSM that a release job needs
        to be created.

        project is the name of the project
        dynamic is a dictionary of dynamic elements to pass through
        exchange is the MQ exchange to emit on. Default: re
        topic is the MQ topic to emit on. Default: job.create
        """
        # Set up the reply-to to our temporary queue
        properties = pika.spec.BasicProperties()
        properties.reply_to = self._tmp_q.method.queue

        self.logger.info('Creating a job for project %s using exchange '
                         '%s and topic %s. Temp queue name is %s '
                         'for request id %s' % (
                             project, exchange, topic,
                             self._tmp_q.method.queue, self.request_id))

        try:
            # Send the message
            self.logger.debug(
                'Sending job request for project %s using exchange '
                '%s and topic %s for request id %s' % (
                    project, exchange, topic, self.request_id))

            msg = {'project': project}

            if dynamic and type(dynamic) is dict:
                msg['dynamic'] = dynamic

            self.logger.debug('Message for %s: %s' % (self.request_id, msg))

            self._channel.basic_publish(
                exchange,
                topic,
                json.dumps(msg), properties=properties)

            self.logger.info(
                'Job request sent for request id %s' % (
                    self.request_id))
        except pika.exceptions.ChannelClosed:
            self.logger.error(
                'Unable to send the message. Channel is closed. '
                'request id %s' % self.request_id)

    def get_confirmation(self, project, exchange='re'):
        """
        Gets a confirmation that the release job has been accepted
        and started.

        project is the name of the project
        exchange is the MQ exchange to emit on. Default: re
        """
        self.logger.info(
            'Listening for response on temp queue %s for request id %s' % (
                self._tmp_q.method.queue, self.request_id))

        for method_frame, header_frame, body in self._channel.consume(
                self._tmp_q.method.queue):
            self.logger.debug('Message received: %s for request id %s' % (
                body, self.request_id))
            try:
                self.logger.info('Parsing bus response for request id %s' % (
                    self.request_id))
                job_id = json.loads(body)['id']
                self._channel.basic_ack(method_frame.delivery_tag)
                self.logger.info('Got job id of %s for request id %s' % (
                    job_id, self.request_id))

                # Send out a notification that the job has been created.
                properties = pika.spec.BasicProperties(app_id='rerest')
                self._channel.basic_publish(
                    exchange,
                    'notification',
                    json.dumps({
                        'slug': 'Started %s' % job_id,
                        'message': "Project %s's job %s has been started." % (
                            project, job_id),
                        'phase': 'created',
                    }),
                    properties=properties)
                return job_id
            except ValueError, vex:
                self.logger.info(
                    'Rejecting bus response due to error for '
                    'request id %s' % self.request_id)
                self._channel.basic_reject(method_frame.delivery_tag)
                self.logger.error(
                    'Could not load JSON message. '
                    'Rejecting message. Error: %s for request id %s' % (
                        vex, self.request_id))
            except pika.exceptions.ChannelClosed:
                self.logger.error(
                    'The channel has unexpectedly closed. request id %s' % (
                        self.request_id))
            finally:
                self.logger.debug('Closed bus connection. request id %s' % (
                    self.request_id))
                try:
                    self._channel.close()
                except pika.exceptions.ChannelClosed:
                    self.logger.debug(
                        'Channel was alread closed. request id %s' % (
                            self.request_id))
