#!/usr/bin/python
from SimpleXMLRPCServer import SimpleXMLRPCServer

def hello(msg):
    return 'Hello you too! This is simple XML-RPC server for kts46.' +\
        '\nYou\'ve said: [' + msg + ']'

# Create and configure server.
server = SimpleXMLRPCServer( ('localhost', 46210) )

# Register functions.
server.register_function(hello)

# Run server.
print('Serving...')
server.serve_forever()
