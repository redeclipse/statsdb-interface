from flask import render_template


def default_error_handler(error):
    """
    Default error handler.

    It is generally a better style to create Flask error handlers for
    exception classes, except for the few HTTP status codes that are not
    produced by exceptions but e.g. the :meth:`flask.abort` function (like
    for example 404).

    This error handler is universal and can be used with all HTTP error codes.

    Example usage::
        for status_code in range(400, 600):
            app.errorhandler(status_code)(default_error_handler)
    """

    # try to read status code and message from the error passed to the
    # exception handler
    if hasattr(error, "code"):
        code = error.code
        name = error.name
        description = error.description

    # otherwise use sane default values, taken from Flask's error database
    else:
        code = 500
        name = "Internal Server Error"
        description = "The server encountered an internal error and was " \
                      "unable to complete your request. Either the server " \
                      "is overloaded or there is an error in the application."

    # build error message and return the rendered error page
    return render_template("error.html", code=code, name=name,
                           description=description), code


def setup_app(app):
    """
    Registers the default error handler for all user and server error codes.

    :param app: A Flask app
    """

    for status_code in range(400, 600):
        try:
            app.errorhandler(status_code)(default_error_handler)
        except KeyError:
            pass
