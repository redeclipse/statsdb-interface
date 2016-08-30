# -*- coding: utf-8 -*-
import statsdbinterface
import config
import sys

# Check for data_directory argument.
if len(sys.argv) < 2:
    print("Usage: %s <data directory>" % sys.argv[0])
    sys.exit(1)

# Set data_directory variable from arguments.
config.data_directory = sys.argv[1]

# Start server.
statsdbinterface.server.run(host=config.HOST, port=config.PORT, debug=True)
