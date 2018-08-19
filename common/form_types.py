from datetime import datetime
from backend.app import app
import json


def ISODateType(date_str):
    try:
        date_object = datetime.strptime(date_str, app.config["DATE_FORMAT"]).date()

        return date_object

    except Exception:
        raise ValueError("Wrong date format.")
