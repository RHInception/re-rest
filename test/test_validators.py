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

from jsonschema import ValidationError

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
            ValidationError, validate_playbook, {'project': '', 'steps': []})
        self.assertRaises(
            ValidationError, validate_playbook,
            {'project': '', 'ownership': ''})
        self.assertRaises(
            ValidationError, validate_playbook, {'steps': [], 'ownership': ''})

        # Steps must have name, plugin and parameters
        self.assertRaises(
            ValidationError,
            validate_playbook,
            {'project': '', 'ownership': '', 'steps': [
                {'name': '', 'parameters': {}}]})

        self.assertRaises(
            ValidationError,
            validate_playbook,
            {'projet': '', 'ownership': '', 'steps': [
                {'name': '', 'plugin': ''}]})

        self.assertRaises(
            ValidationError,
            validate_playbook,
            {'project': '', 'ownership': '', 'steps': [
                {'plugin': '', 'parameters': {}}]})

        # Parameters must be a dict
        self.assertRaises(
            ValidationError,
            validate_playbook,
            {'project': '', 'ownership': '', 'steps': [
                {'name': '', 'plugin': '', 'parameters': ''}]})

    def test_validate_playbook_with_good_data(self):
        """
        Verify validate_playbook does not raise when good data is passed in
        """
        top = {
            'project': 'p',
            'ownership': {'id': 'my team', 'contact': 'me@example.com'},
            'steps': [],
        }
        assert validate_playbook(top) is None

        w_steps = top
        w_steps['steps'].append({
            'name': 'step', 'plugin': 'test', 'parameters': {}})
        assert validate_playbook(w_steps) is None

        w_params = w_steps
        w_params['steps'][0]['parameters'] = {
            'command': 'ls', 'something': 'else'}
        assert validate_playbook(w_params) is None
