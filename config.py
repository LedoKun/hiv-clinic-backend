"""
Config for backend server
Changes as needed!
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")

    # Logger
    # 'always' (default), 'never',  'production', 'debug'
    LOGGER_HANDLER_POLICY = os.environ.get("LOGGER_HANDLER_POLICY")
    LOGGER_NAME = os.environ.get("LOGGER_NAME")

    # Database config
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get(
        "SQLALCHEMY_TRACK_MODIFICATIONS"
    )

    # Form Valification
    BUNDLE_ERRORS = True

    # Data Pagination
    MAX_PAGINATION = int(os.environ.get("MAX_PAGINATION"))
    MAX_SEARCH_RESULT = int(os.environ.get("MAX_SEARCH_RESULT"))
