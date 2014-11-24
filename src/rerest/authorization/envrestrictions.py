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
Default group to environment callables.
"""

from flask import current_app, g
from bson import ObjectId
from rerest.contextfilter import ContextFilter


def environment_allow_all(username, playbook, maplist):  # pragma: no cover
    """
    Helpful when debugging locally. Don't use this in production.
    """
    ContextFilter.set_field('user_id', username)
    ContextFilter.set_field('playbook_id', playbook)
    return True


def environment_flat_files(username, playbook, maplist):
    """
    Opens a flat file when checking for environments.
    """
    ContextFilter.set_field('user_id', username)
    ContextFilter.set_field('playbook_id', playbook)
    try:
        envcfg = current_app.config['ENVIRONMENT_FLAT_FILES']
        groupcfg = current_app.config['GROUP_ENVIRONMENT_MAPPING']
    except KeyError:
        current_app.logger.warn(
            'No ENVIRONMENT_FLAT_FILES set in config. Denying everything.')
        return False

    allowed_envs = []
    for m in maplist:
        try:
            allowed_envs += groupcfg[m]
        except Exception, ex:
            # If the group doesn't exist, that's fine, add nothing
            current_app.logger.debug(
                'Environment %s has no mapping. Skipping...' % m)

    # Remove dupes
    allowed_envs = set(allowed_envs)
    current_app.logger.info(
        'User %s has access the following environments: %s' % (
            username, ', '.join(allowed_envs)))
    # Populate hosts with everything the playbook wants to touch
    hosts = []
    hostinfo = g.db.re.playbooks.find({
        '_id': ObjectId(playbook)}, {'execution.hosts': True})
    for row in hostinfo:
        for hostdata in row['execution']:
            hosts = hosts + hostdata['hosts']

    # Remove dupes
    hosts = list(set(hosts))

    # Check the files
    for env_name, file_path in envcfg.items():
        if env_name in allowed_envs:
            current_app.logger.debug(
                '%s has access to %s' % (username, env_name))
            with open(file_path, 'r') as env_file:
                env_hosts = set(env_file.read().split('\n'))
                hosts = list(set(hosts) - env_hosts)

    # If there is nothing in the hosts list then they have access to
    # everything they requested
    if len(hosts) == 0:
        return True
    # If any hosts still are in the list that means the user does not have
    # access to them!!!!
    current_app.logger.warn(
        'User %s attempted to modify the following hosts via playbook %s but '
        'does not have permission: %s' % (
            username, playbook, ", ".join(hosts)))
    return False
