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
    }
,)
