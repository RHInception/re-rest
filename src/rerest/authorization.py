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


def no_authorization(username, params):  # pragma nocover
    """
    Helpful when debugging locally. Don't use this in production.
    """
    return True


def ldap_search(username, params):
    """
    Searches ldap for a user and then matches and tries to match up an ldap
    field to a lookup.
    """
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
        current_app.logger.debug('LDAP search result: %s' % search_results)
        if len(search_results) >= 1:
            for search_result in search_results:
                try:
                    key = search_result[1][cfg['LDAP_FIELD_MATCH']]
                    # a 1 item list is dumb
                    if type(key) is list and len(key) == 1:
                        key = key[0]
                    allowed_groups = cfg['LDAP_LOOKUP_TABLE'][key]

                    current_app.logger.debug(
                        'User %s has access to the following groups: %s' % (
                            username, allowed_groups))
                    # Using * means the user will have access to everything
                    if '*' in allowed_groups or params['group'] in allowed_groups:
                        current_app.logger.debug(
                            'User %s successfully authenticated for group %s.' % (
                                username, params['group']))
                        return True  # <-- the ONLY return True that should exist!
                    else:
                        current_app.logger.warn(
                            'User %s attempted to access %s though the user is not'
                            ' in the correct group.' % (
                                username, params['group']))
                except KeyError, ke:
                    current_app.logger.error(
                        'Key was missing: %s. Denying auth for user %s' % (
                            ke, username))
        else:
            current_app.logger.error(
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
    return False
