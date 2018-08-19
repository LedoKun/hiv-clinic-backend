"""
Custom JSON Encoder
"""

from flask.json import JSONEncoder
from datetime import date


class CustomJSONEncoder(JSONEncoder):
    """
    Change behaviour of jsonify for some objects
    """

    def default(self, o):
        if isinstance(o, date):
            return o.isoformat()

        return super().default(o)
