from flask_restful import Resource
from backend.models import Patient, Appointment
from flask import jsonify, abort, request
from backend.app import app, db, logger
from sqlalchemy import exc
from webargs import fields
from webargs.flaskparser import parser
from flask_jwt_extended import jwt_required


class AppointmentResource(Resource):
    @jwt_required
    def get(self):
        # Get query info
        query_date = self.search_args()

        try:
            appointments = (
                db.session.query(Appointment)
                .join(Patient, Patient.id == Appointment.paitent_id)
                .filter(Appointment.date == query_date["date"])
                .with_entities(Patient, Appointment)
                .paginate(
                    page=query_date["page"],
                    per_page=app.config["MAX_PAGINATION"],
                )
            )

            logger.debug(
                "Getting appointments on {}".format(query_date["date"])
            )

            return jsonify(
                {
                    "items": appointments.items,
                    "page": appointments.page,
                    "pages": appointments.pages,
                    "total": appointments.total,
                    "perPage": app.config["MAX_PAGINATION"],
                }
            )

        except (IndexError, exc.SQLAlchemyError) as e:
            logger.error("Unable to write to DB")
            logger.error(e)
            abort(500)

    def search_args(self):
        args = {
            "date": fields.Date(required=True),
            "page": fields.Int(missing=1),
        }

        # Phrase args data
        data = parser.parse(args, request)
        return data
