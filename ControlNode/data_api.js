var mongodb = require("mongodb"),
    fluentMongodb = require("./mongodb-fluent"),
    ProjectStorage = require('./projectStorage').Storage,
    mimeTypes = require('./mimeTypes').ext2type;

var parseData = function(data, options, response) {
    if (options.type === 'csv' || options.type === 'tsv') {
        var type = mimeTypes['.'+options.type],
            disposition = "attachment;filename=ServerStatus."+options.type;
        response.writeHead(200, {'Content-Type': type,
                           'Content-disposition': disposition});

        var sep = options.type === 'csv' ? ',' : '\t';
        response.write(['Project', 'Job', 'Done', 'Total steps',
            'Basic statistics', 'Idle times', 'Throughput', 'Full statistics'
            ].join(sep)+"\n");
        data.forEach(function(it){
            response.write([it.project, it.name, it.done, it.totalSteps,
                it.basicStatistics, it.idleTimes, it.throughput,
                it.fullStatistics].join(sep)+"\n");
        });
        response.end();
    } else if (options.type === 'jsonp') {
        response.writeHead(200, {'Content-Type': mimeTypes['.js']});
        response.end([options.callback, "(", JSON.stringify(data), ")"].join(""));
    } else {
        response.writeHead(200, {'Content-Type': mimeTypes['.json']});
        response.end(JSON.stringify(data));
    }
};


/**
  * Gets current server status. Writes result in the requested format.
  *
  * @param storage - Database storage.
  * @param query - Request query options.
  * @param response - Response to client.
  */
var serverStatus = function(storage, query, response){
    storage.getStatus(
        function(d){ parseData(d, query, response); },
        function(err){ console.log(err); process.exit(1); }
    );
};

exports.serverStatus = serverStatus;
