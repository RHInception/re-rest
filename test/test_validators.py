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

from . import TestCase, unittest

from jsonschema import ValidationError, SchemaError

from rerest.validators import validate_playbook


class TestValidators(TestCase):

    def test_validate_playbook_with_missing_items(self):
        """
        Verify validate_playbook checks for expected input and raises
        if missing
        """
        # A playbook must be a dictionary
        self.assertRaises(ValidationError, validate_playbook, [])

        # Missing top level keys should raise
        self.assertRaises(ValidationError, validate_playbook, {})
        self.assertRaises(
            ValidationError, validate_playbook, {'group': '', 'execution': []})
        self.assertRaises(
            ValidationError, validate_playbook,
            {'name': '', 'execution': ''})
        self.assertRaises(
            ValidationError, validate_playbook, {'group': [], 'name': ''})

        # Execution must have description, hosts and steps
        self.assertRaises(
            ValidationError,
            validate_playbook,
            {'name': '', 'group': '', 'execution': [
                {'description': '', 'hosts': ['']}]})

        self.assertRaises(
            ValidationError,
            validate_playbook,
            {'name': '', 'group': '', 'execution': [
                {'hosts': [''], 'steps': ['']}]})

        self.assertRaises(
            ValidationError,
            validate_playbook,
            {'name': '', 'group': '', 'execution': [
                {'steps': [''], 'description': ''}]})

        # There must be at least 1 step and 1 host
        self.assertRaises(
            ValidationError,
            validate_playbook,
            {'name': '', 'group': '', 'execution': [
                {'steps': [''], 'description': '', 'hosts': []}]})

        self.assertRaises(
            ValidationError,
            validate_playbook,
            {'name': '', 'group': '', 'execution': [
                {'steps': [], 'description': '', 'hosts': ['']}]})

    def test_validate_playbook_with_good_data(self):
        """
        Verify validate_playbook does not raise when good data is passed in
        """
        top = {
            'group': 'p',
            'name': 'myplaybook',
            'execution': [{
                'description': 'something',
                'hosts': ['127.0.0.1'],
                'steps': [{"service:Restart": {"service": "httpd"}}]
            }]

        }
        assert validate_playbook(top) is None

        w_steps = top
        # Additional bjects as steps should be valid
        w_steps['execution'].append({
            'description': 'second',
            'hosts': ['127.0.0.1'],
            'steps': [{"service:Restart": {"service": "httpd"}}]})

        # A string as a step should be valid
        w_steps['execution'][0]['steps'].append("do:SomethingAsString")

        assert validate_playbook(w_steps) is None

        # Preflight is optional but should be allowed
        w_steps['execution'][0]['preflight'] = [
            'something:ToDo', {'another:Item': {'with': 'parameters'}}]
        assert validate_playbook(w_steps) is None
