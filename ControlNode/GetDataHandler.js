/*
Copyright 2010-2011 Anthony Kolesov

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

var mimeTypes = require('./mimeTypes').ext2type

function hasData(options, response, data){
    if (options.type === 'csv' || options.type === 'tsv') {
        if (options.method !== "serverStatus") {
            response.writeHead(400, {'Content-Type': mimeTypes['.txt']});
            response.end("This output data type is not supported for this method.");
            return;
        }

        var type = mimeTypes['.'+options.type];
        //    disposition = "attachment;filename=ServerStatus."+options.type;
        response.writeHead(200, {'Content-Type': type});
        //                   'Content-disposition': disposition});

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
}

function onError(response, err) {
    console.log(err);
    response.writeHead(500, "Error getting data from database.")
}

// All methods must be in format function(callback(data), callback(error)). */
function handleRequest(options, response, methods){
    if ("method" in options){
        if (options.method in methods) {
            methods[options.method](options,
                                    hasData.bind({}, options, response),
                                    onError.bind({}, response)  );
        } else {
            response.writeHead(404, {"Content-type": mimeTypes[".txt"]});
            response.end("Unknown method: " + options.method);
        }
    } else {
        response.writeHead(400, {"Content-type": mimeTypes[".txt"]});
        response.end("Missing `method` parameter.");
    }
}

exports.handle = handleRequest;
