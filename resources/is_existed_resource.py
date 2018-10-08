from flask_restful import Resource
from backend.models import Patient
from flask import jsonify, abort, request
from backend.app import db, logger
from sqlalchemy import func
from webargs import fields
from marshmallow import validate, ValidationError
from webargs.flaskparser import parser


class IsExistedResource(Resource):
    def get(self):
        # Get query info
        search_args = self.search_args()

        try:
            column = getattr(Patient, search_args["field"])

            hn = (
                Patient.query.with_entities(Patient.hn)
                .filter(column == search_args["query"])
                .first()
            )

        except (AttributeError, TypeError) as e:
            logger.error("Unable to connect to the DB.")
            logger.error(e)
            abort(409)

        logger.debug(
            "Check for uniqueness using Patient model, column: {}, filter: {}, hn: {}.".format(
                search_args["field"], search_args["query"], str(hn)
            )
        )

        return jsonify({"result": bool(hn)})

    def search_args(self):
        args = {
            "field": fields.String(
                required=True, validate=validate.OneOf(Patient.__unique__)
            ),
            "query": fields.String(required=True),
        }

        # Phrase args data
        data = parser.parse(args, request)

        return data
