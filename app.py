"""
Glue for backend server
"""

from flask import Flask
from flask_restful import Api
from backend.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

# Setup application
app = Flask(__name__)
app.config.from_object(Config)

# Setup logger
logger = app.logger

# Setup DB
db = SQLAlchemy(app)
from backend import models          # noqa

migrate = Migrate(app, db)

# Setup flask-resful
api = Api(app)

# JWT
jwt = JWTManager(app)

# Import other helper scripts
from backend import resource        # noqa
from backend import errors          # noqa
import backend.common.jwt           # noqa

# Initialize ICD10 database
import backend.common.index_icd10   # noqa

# Use CustomJSONEncoder
from backend.common.json_encoder import CustomJSONEncoder   # noqa

app.json_encoder = CustomJSONEncoder
