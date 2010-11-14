"""
License:
   Copyright 2010 Anthony Kolesov

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

definitions = (
    { "doc": "basicStats", "view": "addCar",
        "map": """
        function(doc) {
            // car creations
            for (var id in doc.cars){
                if (doc.cars[id].state && doc.cars[id].state === 'add') {
                    emit(id, {'time': doc.time});
                }
            }
        }"""
    },
    {
        "doc": "basicStats", "view": "deleteCar",
        "map": """
        function(doc) {
            for (var id in doc.cars){
                if (doc.cars[id].state && doc.cars[id].state === 'del') {
                    emit(id, {'time': doc.time});
                }
            }
        }
        """
    },
    {
        "doc": "manage", "view": "jobs",
        "map": """
        function(doc) {
            if (doc.type === 'job'){
                emit(doc.name, doc._id);
            }
        }
        """
    },
    {
        "doc": "manage", "view": "states",
        "map":"""
            function(doc) {
                if (doc.type === 'state')
                    emit(doc.job, doc._id);
            }
        """
    }
)
