# -*- coding: utf-8 -*-
from statsdbinterface import server
from flask import jsonify


# Return a simple Not Found message upon 404.
@server.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found',
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp
