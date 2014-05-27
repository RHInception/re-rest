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
Validation functions.
"""

from jsonschema import ValidationError, validate


#: Schema for playbook defined by using json-schema.org syntax.
PLAYBOOK_SCHEMA = {
    'type': 'object',
    'required': ['project', 'ownership', 'steps'],
    'properties': {
        'project': {'type': 'string'},
        'ownership': {
            'type': 'object',
            'properties': {
                'id': {'type': 'string'},
                'contact': {'type': 'string'},
            },
        },
        'steps': {
            'type': 'array',
            'items': [{
                'type': 'object',
                'additionalItems': False,
                'required': ['name', 'plugin', 'parameters']}],
        },
    }
}


validate_playbook = lambda pb: validate(pb, PLAYBOOK_SCHEMA)
