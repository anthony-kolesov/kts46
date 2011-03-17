****************
Node modules API
****************

staticFileHandler
=================

.. js:function:: handle(filesDirectory, pathPrefix, request, response)

    Handles request for a static file.

    :param string filesDirectory: Root directory of static files.
    :param string pathPrefix: Prefix for static files in the request path.
    :param request: Client request to serve.
    :param response: Server to response to return.


mimeTypes
=========

Map of file extensions to MIME types. These are taken from Python ``mimetypes``
standard library.

.. js:attribute:: ext2type

    Map of extensions to types (``string`` => ``string``). All extensions start
    with dot (i.e. ``.css``).
