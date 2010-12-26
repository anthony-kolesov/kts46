import sys
sys.path.append('../lib/')
import kts46.utils
from kts46.server.json_api import JSONApiServer


cfg = kts46.utils.getConfiguration(('../config/json_api.ini',))
s = JSONApiServer(cfg)
s.server_forever()

