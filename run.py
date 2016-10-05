#! /usr/bin/env python3

import os
import sys

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from statsdbinterface import app_factory


def create_app(data_dir):
    """
    Create an app from a (potentially) relative path.
    """

    data_dir = os.path.join(os.path.abspath(os.curdir), data_dir)

    # Validate commandline parameters
    if not os.path.isdir(data_dir):
        raise RuntimeError("No such directory: %s" % data_dir)

    if not os.path.isfile(os.path.join(data_dir, "stats.sqlite")):
        raise RuntimeError("Could not find stats.sqlite in %s" % data_dir)

    # Create a new Flask app instance and apply the configuration
    return app_factory.create_app(data_dir)


if __name__ == "__main__":
    # Check for data_directory argument.
    if len(sys.argv) < 2:
        print("Usage: %s <data directory>" % sys.argv[0])
        sys.exit(1)

    app = create_app(sys.argv[1])

    # Start server
    if app.config['DEBUG']:
        # Use Flask's debugging server.
        app.run(host=app.config['HOST'], port=app.config['PORT'], debug=True)
    else:
        # Use Tornado's HTTPServer.
        http_server = HTTPServer(WSGIContainer(app))
        http_server.listen(address=app.config['HOST'], port=app.config['PORT'])
        IOLoop.instance().start()
