/*  Copyright 2010-2011 Anthony Kolesov

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

var url = require("url"),
    mimeTypes = require("./mimeTypes").ext2type,
    path = require("path"),
    fs = require("fs");

/**
 * Handles request for static file.
*/
var handle = function(filesDirectory, pathPrefix, request, response){
    var uri = url.parse(request.url).pathname;
    if (pathPrefix.length > 0 && uri.indexOf(pathPrefix) === 0) {
        uri = uri.substring(pathPrefix.length);
    }
    var filename = path.join(filesDirectory, uri);

    path.exists(filename, function(exists) {
        if(!exists) {
            response.writeHead(404, {"Content-Type": "text/plain"});
            response.end("404 Not Found\n");
            return;
        }
        fs.readFile(filename, "binary", function(err, file) {
            if(err) {
                response.writeHead(500, {"Content-Type": "text/plain"});
                response.end(err + "\n");
                return;
            }

            var mimeType = "text/plain",
                extension = path.extname(filename);
            if (extension in mimeTypes) {
                mimeType = mimeTypes[extension];
            }
            response.writeHead(200, {"Content-Type": mimeType});
            response.end(file, "binary");
        });
    });
};

exports.handle = handle;
