#!/usr/bin/env python
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
Build script.
"""

import os.path

try:
    from setuptools import setup, find_packages
except ImportError:
    import warnings
    warnings.warn('No setuptools. Script creation will be skipped.')
    from distutils.core import setup

def parse_requirements(path):
    with open(path, 'r') as install_reqs:
        return install_reqs.read().splitlines()

reqs = parse_requirements('requirements.txt')

setup(
    name='rerest',
    version='0.0.6-2',
    description="REST entrypoint to the core component of the Inception Release Engine",
    author='See AUTHORS',
    author_email='inception@redhat.com',
    url='https://github.com/RHInception/re-rest',
    license='AGPLv3',
    zip_safe=False,
    package_dir={
        'rerest': os.path.join('src', 'rerest')
    },
    install_requires=reqs,
    packages=find_packages('src'),
    classifiers=[
        ('License :: OSI Approved :: GNU Affero General Public '
         'License v3 or later (AGPLv3+)'),
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
    ],

)
