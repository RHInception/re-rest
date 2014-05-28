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
import sys
import ldap
import ldap.filter
import mock

from . import TestCase, unittest

from rerest import authorization
from rerest.app import app


class TestAuthorization(TestCase):
    """
    Tests for the authorization callables.
    """

    def test_no_authorization(self):
        """
        no_authorization should always return True.
        """
        assert authorization.no_authorization(None, None)

    def test_ldap_search(self):
        """
        Verify ldap search only allows if a user is in an expected group.
        """
        # Check sunny day searches
        with app.app_context():
            with mock.patch.dict(
                    'sys.modules', {'ldap': mock.MagicMock(ldap)}):
                mldap = sys.modules['ldap']
                conn = mock.MagicMock('conn')
                conn.search_s = mock.MagicMock(
                    return_value=[(
                        'uid=username',
                        {'manager': 'uid=amanager,dc=example,dc=com'},
                    )]
                )
                conn.simple_bind_s = mock.MagicMock('simple_bind_s')
                mldap.initialize.return_value = conn

                assert authorization.ldap_search(
                    'username', {'group': 'group1'})
                assert authorization.ldap_search(
                    'username', {'group': 'notallowed'}) is False

        # Check on error conditions
        # If SERVER_DOWN, LDAPError or ImportError is raised the user should
        # not be able to authorize
        with app.app_context():
            with mock.patch.dict(
                    'sys.modules', {'ldap': mock.MagicMock(ldap)}):
                mldap = sys.modules['ldap']
                for ex in (ImportError, mldap.SERVER_DOWN, mldap.LDAPError):
                    mldap.initialize.side_effect = ex

                    assert authorization.ldap_search(
                        'username', {'group': 'group1'}) is False
                    assert authorization.ldap_search(
                        'username', {'group': 'notallowed'}) is False
