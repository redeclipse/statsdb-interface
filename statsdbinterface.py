#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import config

if __name__ == "__main__":
    # Check for data_directory argument.
    if len(sys.argv) < 2:
        print("Usage: %s <data directory>" % sys.argv[0])
        sys.exit(1)

    # Set data_directory variable from arguments.
    config.data_directory = sys.argv[1]

    # Load the main program after setting required config entries.
    import statsdbinterface

    # Start server.
    if config.DEBUG:
        # Use Flask's debugging server.
        statsdbinterface.server.run(host=config.HOST,
                                    port=config.PORT, debug=True)
    else:
        # Use Tornado's HTTPServer.
        http_server = HTTPServer(WSGIContainer(statsdbinterface.server))
        http_server.listen(address=config.HOST, port=config.PORT)
        IOLoop.instance().start()
