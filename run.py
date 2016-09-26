#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from statsdbinterface import create_app

import config


if __name__ == "__main__":
    # Check for data_directory argument.
    if len(sys.argv) < 2:
        print("Usage: %s <data directory>" % sys.argv[0])
        sys.exit(1)

    # Set data_directory variable from arguments.
    config.data_directory = sys.argv[1]

    # Create a new Flask app instance and apply the configuration
    app = create_app(config)

    # Start server
    if config.DEBUG:
        # Use Flask's debugging server.
        app.run(host=config.HOST, port=config.PORT, debug=True)
    else:
        # Use Tornado's HTTPServer.
        http_server = HTTPServer(WSGIContainer(app))
        http_server.listen(address=config.HOST, port=config.PORT)
        IOLoop.instance().start()
