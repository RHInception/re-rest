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
Default authorization callables.
"""

from flask import current_app
from rerest.contextfilter import ContextFilter


def no_authorization(username, params):  # pragma nocover
    """
    Helpful when debugging locally. Don't use this in production.
    """
    ContextFilter.set_field('user_id', username)
    return (True, [])


def ldap_search(username, params):
    """
    Searches ldap for a user and then matches and tries to match up an ldap
    field to a lookup.
    """
    ContextFilter.set_field('user_id', username)
    try:
        import ldap
        import ldap.filter

        cfg = current_app.config['AUTHORIZATION_CONFIG']

        conn = ldap.initialize(cfg['LDAP_URI'])
        conn.simple_bind_s(
            cfg.get('LDAP_USER', ''), cfg.get('LDAP_PASSWORD', ''))

        search_results = conn.search_s(
            str(cfg['LDAP_SEARCH_BASE']),
            ldap.SCOPE_SUBTREE,
            '(%s=%s)' % (
                str(cfg['LDAP_MEMBER_ID']),
                ldap.filter.escape_filter_chars(username, 1)),
            [str(cfg['LDAP_FIELD_MATCH'])]
        )
        current_app.logger.debug('LDAP search result: %s' % str(search_results))

        allowed_groups = []
        has_access = False
        if len(search_results) >= 1:
            keys = []
            for search_result in search_results:
                keys += search_result[1][cfg['LDAP_FIELD_MATCH']]

            for key in keys:
                try:
                    allowed_groups += cfg['LDAP_LOOKUP_TABLE'][key]

                    # Using * means the user will have access to everything
                    if ('*' in allowed_groups or
                            params['group'] in allowed_groups):
                        current_app.logger.debug(
                            'User %s successfully authenticated for group'
                            ' %s via ldap group %s.' % (
                                username, params['group'], key))
                        # This is the ONLY place that should set True
                        has_access = True

                except KeyError, ke:
                    current_app.logger.debug(
                        'There is no configured info for ldap group '
                        'for %s. Moving on ...' % ke)
            current_app.logger.debug(
                'User %s has access to these groups: %s' % (
                   username, allowed_groups))

            if has_access:
                return (True, keys)
            current_app.logger.warn(
                'User %s attempted to access %s though the user is not'
                ' in the correct group.' % (
                    username, params['group']))

        else:
            current_app.logger.warn(
                'No groups returned. Denying auth for %s.' % (
                    username))

    except ImportError:
        current_app.logger.error(
            'python-ldap not available. Denying all user auth attempts.')
    except ldap.SERVER_DOWN:
        current_app.logger.error(
            'Can not bind to LDAP. Denying all user auth attempts.')
    except ldap.LDAPError, le:
        current_app.logger.error(
            'General ldap error: %s. Denying auth attempt for user %s.' % (
                le, username))
    return (False, [])
