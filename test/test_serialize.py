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
import json
import yaml

from . import TestCase, unittest

from rerest import serialize


class TestSerialze(TestCase):
    """
    Tests for the serialize system.
    """

    def test__init__(self):
        """
        Make sure creating a serialize instance only allows supported formats.
        """
        # By default we should have json.
        s0 = serialize.Serialize()
        assert s0.format == 'json'
        assert s0.mimetype == 'application/json'

        # If we say json it should be json.
        s1 = serialize.Serialize('json')
        assert s1.format == 'json'
        assert s1.mimetype == 'application/json'

        # If we say yaml it should be yaml
        s2 = serialize.Serialize('yaml')
        assert s2.format == 'yaml'
        assert s2.mimetype == 'text/yaml'

        # Anything else should raise an error
        self.assertRaises(ValueError, serialize.Serialize, 'SOMETHINGELSE')

    def test_serialize_json(self):
        """
        JSON de/serialization should work.
        """
        s = serialize.Serialize('json')
        data = {'test': 'test'}
        json_str = s.dump(data)
        assert type(json_str) in (str, unicode)
        python_structure = s.load(json_str)
        assert data == python_structure

    def test_serialize_yaml(self):
        """
        YAML de/serialization should work.
        """
        s = serialize.Serialize('yaml')
        data = {'test': 'test'}
        yaml_str = s.dump(data)
        assert type(yaml_str) in (str, unicode)
        python_structure = s.load(yaml_str)
        assert data == python_structure

    def test_consistent_errors_on_load(self):
        """
        Bad data should cause the same errors on loading.
        """
        # Test loading
        for format in serialize.Serialize._supported:
            s = serialize.Serialize(format)
            self.assertRaises(ValueError, s.load, '[BADDATA')

    def test_consistent_errors_on_dump(self):
        """
        Bad data should cause the same errors on dump.
        """
        # Test dumping
        for format in serialize.Serialize._supported:
            s = serialize.Serialize(format)
            self.assertRaises(ValueError, s.dump, object())
