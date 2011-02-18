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

__version__ = '0.1.5'
__author__ = "Anthony Kolesov"

