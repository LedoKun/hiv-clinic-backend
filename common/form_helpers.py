from datetime import datetime
from pytz import timezone
from backend.app import app


def ISODateType(date_str):
    try:
        date_object = datetime.strptime(
            date_str, app.config["DATE_FORMAT"]
        ).date()

        return date_object

    except Exception:
        raise ValueError("Wrong date format.")


def convert_to_utc(date_obj):
    return date_obj.replace(tzinfo=timezone("UTC"))
