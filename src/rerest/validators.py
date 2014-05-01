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


def validate_playbook(playbook):
    """
    Quick validation of the playbook.

    Raises KeyError on issue.
    """
    # TODO: KeyError makes sens for most of the raises but not all...
    #       Use a new Exception type?
    # Must be a dictionary
    if type(playbook) is not dict:
        raise KeyError('Playbook must be a dictionary')

    # Must have specific keys at the top level
    for key in ('project', 'ownership', 'steps'):
        if key not in playbook.keys():
            raise KeyError(
                'Playbook requires the following top level keys: '
                'project, ownership, steps.')

    # Steps must have specific keys
    for step in playbook['steps']:
        for key in ('name', 'plugin', 'parameters'):
            if key not in step.keys():
                raise KeyError(
                    'Playbook steps require the following keys: '
                    'name, plugin, parameters')

        # Parameters in steps must be a dictionary
        if type(step['parameters']) is not dict:
            raise KeyError(
                'Playbook step parameters must be in a dictionary.')
