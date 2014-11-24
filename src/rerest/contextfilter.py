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
Accumulating logger filter which remembers contextual information
about a users request.
"""
import logging
import datetime
import pytz


class ContextFilter(logging.Filter):
    """This is a filter which injects contextual information into the log.

    Usage follows this pattern:

    When a new piece of log information is discovered or calculated
    call the *Class Method*
    :py:meth:`rerest.contextfilter.ContextFilter.set_field`

    Example: We are waiting to receive a new deployment ID from the
    job creator. We create a log record of our request for a response
    from the job creator. Because this logging event happens prior to
    receiving the deployment id, it can not log this information. The
    record would appear as such:

    > 2014-11-23 21:09:10,193 +1030 - app_component="rerest" - source_ip="127.0.0.1" - log_level="INFO" - playbook_id="542423e102b67c000f941dcb" - deployment_id="" - user_id="justabro" - message="Listening for response on temp queue amq.gen-k5e..."

    Note how the 'deployment_id' field is missing a value.

    Following this message emission we get the deployment id from the
    job creator's get_confirmation method. Inside of get_confirmation
    the following call is made:

    # mq.py
    ContextFilter.set_field('deployment_id', job_id)
    # ...
    return job_id

    New fields were added to the ContextFilter 'my_fields'
    dictionary. As a class variable, field data accumulates until the
    users request is satisfied. As a result, .

    # views.py
    confirmation_id = jc.get_confirmation(group)
    current_app.logger.debug(
        'Confirmation id received for request id %s' % (
            request.request_id))

    If 'abcdefg123456' were the deployment id then the log record
    produced by the debug statement (above) would appear as such:

    > 2014-11-23 21:09:10,732 +1030 - app_component="rerest" - source_ip="127.0.0.1" - log_level="INFO" - playbook_id="542423e102b67c000f941dcb" - deployment_id="abcdefg123456" - user_id="justabro" - message="Confirmation id received for request id abcdefg123456"

    Note how the 'deployment_id' field is automatically filled in.

    See the __main__ stuff below for a code example of how things
    accumulate. Run this source file in an interpreter to watch how
    things accumulate (if you don't believe me).

    ADDITION OF NEW FIELDS:

    To add new fields to the logging format string you must add them
    to the class 'FIELDS' variable.

    """

    FIELDS = ['playbook_id', 'deployment_id', 'app_component', 'user_id', 'source_ip']

    def filter(self, record):
        # We don't use the built-in %(asctime)s formatter because it
        # will omit the TZ offset.

        record.date_string = pytz.UTC.localize(datetime.datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S.%f %z')

        for f in self.FIELDS:
            value = self.my_fields.get(f, '')
            setattr(record, f, value)
        return True

    my_fields = {}

    @classmethod
    def set_field(cls, k, v):
        cls.my_fields[k] = v

if __name__ == '__main__':
    levels = (logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL)
    logging.basicConfig(level=logging.DEBUG,
                        format='%(date_string)s - app_component="%(app_component)s" - source_ip="%(source_ip)s" - log_level="%(levelname)s" - playbook_id="%(playbook_id)s" - deployment_id="%(deployment_id)s" - user_id="%(user_id)s" - message="%(message)s"')

    ContextFilter.set_field('app_component', 'rerest')
    a2 = logging.getLogger('d.e.f')
    f = ContextFilter()
    a2.addFilter(f)
    a2.log(10, 'omfg')

    f.set_field('playbook_id', '1234567890')
    a2.log(30, 'bro')
    a2.warn("I can has warn?")

    f.set_field('deployment_id', '0987654321')
    a2.info("I can has info?")
    a2.log(20, 'bro, look')

    f.set_field('user_id', 'abro')
    f.set_field('source_ip', '192.168.157.13')
    a2.log(10, 'sweet log right?')
