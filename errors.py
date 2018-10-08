"""
JSON Error Handlers
Replace default error handlers with JSON equivalents
Add additional error handlers as needed
"""

from werkzeug.exceptions import HTTPException
from flask.json import jsonify
from backend.app import app, logger
from webargs.flaskparser import parser
from flask import abort


# This error handler is necessary for usage with Flask-RESTful
@parser.error_handler
def handle_request_parsing_error(err, req, schema):
    """webargs error handler that uses Flask-RESTful's abort function to return
    a JSON error response to the client.
    """
    logger.debug(err)
    abort(422)


def error_handler(error):
    """
    Standard Error Handler
    """
    if isinstance(error, HTTPException):
        error_payload = {
            "statusCode": error.code,
            "name": error.name,
            "description": error.description,
        }

        logger.debug(error, HTTPException)

        return (jsonify(error_payload), error.code)
    else:
        return (
            jsonify(
                {
                    "statusCode": 500,
                    "name": "Internal Server Error",
                    "description": "An unknown error has occurred",
                }
            ),
            500,
        )


# common errors - add others as needed
app.register_error_handler(400, error_handler)
app.register_error_handler(401, error_handler)
app.register_error_handler(403, error_handler)
app.register_error_handler(404, error_handler)
app.register_error_handler(405, error_handler)
app.register_error_handler(422, error_handler)
app.register_error_handler(500, error_handler)
