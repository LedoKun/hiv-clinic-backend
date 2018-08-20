"""
Config for backend server
Changes as needed!
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = (
        os.environ.get("SECRET_KEY")
        or "hefiw4peechai4aoph5gazeevei6quahsh7pis7Zeitoo5sae7aedeetha6raiW3eZoth0quie2PeXohkie1Ozeiraisaal7eyah"
    )

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "backend.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 'always' (default), 'never',  'production', 'debug'
    LOGGER_HANDLER_POLICY = "debug"
    LOGGER_NAME = "femmapi"

    # Form Valification
    BUNDLE_ERRORS = True
    DATE_FORMAT = "%Y-%m-%d"
