# -*- coding: utf-8 -*-

# License:
#
#Copyright 2010-2011 Anthony Kolesov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""This package contains all modules of kts46 - traffic simulation system.
This simulation system is distributed and consists of separate components
that run on nodes. One node can host several or one component. In extreme
cases all components of system can run on one node.

Mongodb is used as a storage and proper connection settings must be provided
in :file:`config/local.ini` file. For simulation those python packages are required:

* ``numpy``
* ``pyYAML``
* ``pymongo``

"""


import yaml
from datetime import timedelta # for YAML

__version__ = '0.1.4'
__author__ = "Anthony Kolesov"


# Init YAML staff.
def _timedeltaYAMLRepresenter(dumper, data):
    # Only days, seconds and microseconds are stored internally.
    fmt = u'{0}d{1}s{2}'
    value = fmt.format(data.days, data.seconds, data.microseconds)
    return dumper.represent_scalar(u'!timedelta', value)

def _timedeltaYAMLConstructor(loader, node):
    value = loader.construct_scalar(node)
    days, rest = value.split('d')
    seconds, mcs = rest.split('s')
    return timedelta(days=int(days), seconds=int(seconds), microseconds=int(mcs))

# It is required to explicitly specify SafeLoader or this loader will not see
# constructor.
yaml.add_constructor(u'!timedelta', _timedeltaYAMLConstructor, yaml.SafeLoader)
yaml.add_representer(timedelta, _timedeltaYAMLRepresenter)
