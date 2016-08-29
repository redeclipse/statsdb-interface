# -*- coding: utf-8 -*-
import statsdbinterface
import config

# Start server
statsdbinterface.server.run(host=config.HOST, port=config.PORT, debug=True)
