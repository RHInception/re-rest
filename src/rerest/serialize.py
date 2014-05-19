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
Serialization abstraction.
"""

import yaml

from flask import json


class Serialize(object):
    """
    Serializes both json and yaml in one interface.
    """

    #: Supported serializers
    _supported = ['json', 'yaml']

    def __init__(self, format='json'):
        """
        Creates the serializer instance.
        """
        format = format.lower()
        if format not in self._supported:
            raise ValueError('The following are supported: %s' % (
                self._supported))
        self.format = format

    def load(self, data):
        """
        Loads serialized data into a python structure.
        """
        if self.format == 'yaml':
            try:
                return yaml.safe_load(data)
            except yaml.parser.ParserError, pe:
                raise ValueError(str(pe))
        try:
            return json.loads(data)
        except ValueError, ve:
            raise ValueError(str(ve))

    def dump(self, data):
        """
        Dumps a python structure into a serialized fromat.
        """
        if self.format == 'yaml':
            try:
                return yaml.safe_dump(data, default_flow_style=False)
            except yaml.representer.RepresenterError, re:
                raise ValueError(str(re))
        try:
            return json.dumps(data, indent=1)
        except TypeError, te:
            raise ValueError(str(te))

    @property
    def mimetype(self):
        """
        Returns the proper mimetype
        """
        if self.format == 'yaml':
            return 'text/yaml'
        return 'application/json'
