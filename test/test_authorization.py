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

from flask import g
from rerest.authorization import callables, envrestrictions
from rerest.app import app


class TestAuthorizationCallables(TestCase):
    """
    Tests for the authorization callables.
    """

    def test_no_authorization(self):
        """
        no_authorization should always return True.
        """
        assert callables.no_authorization(None, None)

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
                    return_value=[[
                        'cn=someldapgroup,dc=example,dc=com',
                        {'cn': ['someldapgroup']},
                    ]]
                )
                conn.simple_bind_s = mock.MagicMock('simple_bind_s')
                mldap.initialize.return_value = conn

                r = callables.ldap_search(
                    'username', {'group': 'group1'})
                print r
                assert r[0]
                assert callables.ldap_search(
                    'username', {'group': 'notallowed'})[0] is False

        # Check on error conditions
        # If SERVER_DOWN, LDAPError or ImportError is raised the user should
        # not be able to authorize
        with app.app_context():
            with mock.patch.dict(
                    'sys.modules', {'ldap': mock.MagicMock(ldap)}):
                mldap = sys.modules['ldap']
                for ex in (ImportError, mldap.SERVER_DOWN, mldap.LDAPError):
                    mldap.initialize.side_effect = ex

                    assert callables.ldap_search(
                        'username', {'group': 'group1'})[0] is False
                    assert callables.ldap_search(
                        'username', {'group': 'notallowed'})[0] is False

    def test_ldap_search_for_unconfigured_group_fails(self):
        """
        Verify that if the ldap group is not configured access is not granted
        """
        with app.app_context():
            with mock.patch.dict(
                    'sys.modules', {'ldap': mock.MagicMock(ldap)}):
                mldap = sys.modules['ldap']
                conn = mock.MagicMock('conn')
                conn.search_s = mock.MagicMock(
                    return_value=[(
                        'cn=thisdoesnotexist,dc=example,dc=com',
                        {'cn': 'thisdoesnotexist'},
                    )]
                )
                conn.simple_bind_s = mock.MagicMock('simple_bind_s')
                mldap.initialize.return_value = conn

                assert callables.ldap_search(
                    'username', {'group': 'group1'})[0] is False
                assert callables.ldap_search(
                    'username', {'group': 'notallowed'})[0] is False

    def test_ldap_search_with_wildcard_access(self):
        """
        Verify user has access to all groups if they have * listed.
        """
        # Check sunny day searches
        with app.app_context():
            with mock.patch.dict(
                    'sys.modules', {'ldap': mock.MagicMock(ldap)}):
                mldap = sys.modules['ldap']
                conn = mock.MagicMock('conn')
                conn.search_s = mock.MagicMock(
                    return_value=[(
                        'cn=superadmins,dc=example,dc=com',
                        {'cn': 'superadmins'},
                    )]
                )
                conn.simple_bind_s = mock.MagicMock('simple_bind_s')
                mldap.initialize.return_value = conn

                assert callables.ldap_search(
                    'username', {'group': 'group1'})
                assert callables.ldap_search(
                    'username', {'group': 'howaboutthis'})


class TestAuthorizationEnvRestrictions(TestCase):
    """
    Tests for the environment restriction callables.
    """

    def test_environment_allow_all(self):
        """
        environment_allow_all always returns True.
        """
        assert envrestrictions.environment_allow_all('user', '', [])

    def test_environment_flat_files(self):
        """
        Verify ldap search only allows if a user is in an expected group.
        """
        with app.app_context():
            with mock.patch('pymongo.MongoClient') as mc:
                mc.db.re.playbooks.find.return_value = [{
                    'execution': [{'hosts': ['host10']}]}]
                g.db = mc.db
                # This grouping should have access
                assert envrestrictions.environment_flat_files(
                    'username', '5408c8b002b67c0013ac3737', ['superadmins'])
                # This grouping should not have access
                assert envrestrictions.environment_flat_files(
                    'username', '5408c8b002b67c0013ac3737', ['someldapgroup']) is False
