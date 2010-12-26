import sys
sys.path.append('../lib/')
from kts46.server.json_api import JSONApiServer

s = JSONApiServer(None)
s.server_forever()

