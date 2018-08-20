"""
Custom JSON Encoder
"""

from flask.json import JSONEncoder
from datetime import date
from backend.models import Patient, Visit, Lab, Imaging, Appointment


class CustomJSONEncoder(JSONEncoder):
    """
    Change behaviour of jsonify for some objects
    """

    def default(self, o):
        if isinstance(o, date):
            return o.isoformat()

        elif isinstance(o, (Patient, Visit, Lab, Imaging, Appointment)):
            return o.serialize()

        else:
            return super().default(o)
