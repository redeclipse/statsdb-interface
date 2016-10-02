#! /usr/bin/env python3

import os
import sys

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from statsdbinterface import app_factory

import config


if __name__ == "__main__":
    # Check for data_directory argument.
    if len(sys.argv) < 2:
        print("Usage: %s <data directory>" % sys.argv[0])
        sys.exit(1)

    data_dir = sys.argv[1]

    # Validate commandline parameters
    if not os.path.isdir(data_dir):
        raise RuntimeError("No such directory: %s" % data_dir)

    if not os.path.isfile(os.path.join(data_dir, "stats.sqlite")):
        raise RuntimeError("Could not find stats.sqlite in %s" % data_dir)

    # Set data_directory variable from arguments.
    config.data_directory = data_dir

    # Create a new Flask app instance and apply the configuration
    app = app_factory.create_app(config)

    # Start server
    if config.DEBUG:
        # Use Flask's debugging server.
        app.run(host=config.HOST, port=config.PORT, debug=True)
    else:
        # Use Tornado's HTTPServer.
        http_server = HTTPServer(WSGIContainer(app))
        http_server.listen(address=config.HOST, port=config.PORT)
        IOLoop.instance().start()
