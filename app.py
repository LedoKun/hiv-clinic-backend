"""
Glue for backend server
"""

from flask import Flask
from flask_restful import Api
from backend.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Setup application
app = Flask(__name__)
app.config.from_object(Config)

# Setup logger
logger = app.logger

# Setup DB
db = SQLAlchemy(app)
from backend import models

migrate = Migrate(app, db)

# Setup flask-resful
api = Api(app)

# Import other helper scripts
from backend import resource
from backend import errors

# Initialize ICD10 database
import backend.common.index_icd10

# Use CustomJSONEncoder
from backend.common.json_encoder import CustomJSONEncoder
app.json_encoder = CustomJSONEncoder
