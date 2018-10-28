"""
Custom JSON Encoder
"""

from flask.json import JSONEncoder
from datetime import date, datetime
from backend.models import Patient, Visit, Lab, Imaging, Appointment, ICD10
import pandas as pd
import json


class CustomJSONEncoder(JSONEncoder):
    """
    Change behaviour of jsonify for some objects
    """

    def default(self, o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()

        elif isinstance(o, (Patient, Visit, Lab, Imaging, Appointment, ICD10)):
            return o.serialize()

        elif isinstance(o, pd.DataFrame):
            return [o.columns.tolist()] + o.values.tolist()

        elif isinstance(o, pd.Series):
            return json.loads(
                o.to_json(default_handler=str, date_format="iso")
            )

        elif isinstance(o, (pd.Period, pd.Interval)):
            return str(o)

        else:
            return super().default(o)
