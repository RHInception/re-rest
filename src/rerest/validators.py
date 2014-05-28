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
import os
import json

from jsonschema import ValidationError, validate


#: Schema for playbook defined by using json-schema.org syntax.
playbook_schema_file = os.path.sep.join([
    os.path.split(__file__)[0], 'data', 'playbook_schema.json'])
with open(playbook_schema_file, 'r') as f:
    PLAYBOOK_SCHEMA = json.load(f)


'''PLAYBOOK_SCHEMA = {
    'type': 'object',
    'required': ['group', 'name', 'execution'],
    'properties': {
        'group': {'type': 'string'},
        'name': {'type': 'string'},
        'execution': {
            'type': 'array',
            'items': [{
                'type': 'object',
                'additionalItems': False,
                'required': ['hosts', 'preflight', 'steps']}],
        },
    }
}
'''

#: validated that a playbook meets the expected schema
validate_playbook = lambda pb: validate(pb, PLAYBOOK_SCHEMA)
