"""
Glue for backend server
"""

from flask import Flask
from flask_restful import Api
from backend.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
api = Api(app)
logger = app.logger

# Import other helper scripts
from backend import models
from backend import resource
from backend import errors

# Use CustomJSONEncoder
from backend.common.json_encoder import CustomJSONEncoder

app.json_encoder = CustomJSONEncoder
