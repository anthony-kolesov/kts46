*************
jsonRpcClient
*************

Module of JSON RPC client class.

.. py:class:: jsonRpcClient.RPCException

    Exception that represent error that was returned from JSON RPC server.

.. py:class:: jsonRpcClient.Client

    JSON RPC client. Just call functions and this object will redirect them to
    RPC server.
    
.. py:function:: jsonRpcClient.Client.__init__(self, address, id=1)

    address - address of JSON RPC server, like ``http://example.com:8000/rpc``.
