from flask_restful import Resource, reqparse
from flask import jsonify, abort
from backend.app import db, logger
from backend.common.form_types import ISODateType
from sqlalchemy import exc, exists
from sqlalchemy.orm import load_only
from backend.models import Patient, Visit
import json


class VisitResource(Resource):
    def get(self, hn=None, visit_date=None):

        # Change HN and visit_date format
        if not hn:
            logger.error("No HN supplied.")
            abort(404)

        else:
            hn = hn.replace("^", "/")

        if visit_date:
            try:
                visit_date = ISODateType(visit_date)

            except ValueError as e:
                logger.error("Invalid date format supplied.")
                logger.error(e)
                abort(400)

        # Read from DB
        try:
            patient = Patient.query.filter_by(hn=hn).first()

            if not patient:
                logger.error("No patient with HN {} found.".format(hn))
                abort(404)

            # Return all visits
            if hn and not visit_date:
                logger.debug("Returning all visits by HN {}.".format(hn))
                visits = patient.visits.all()
                return jsonify(visits)

            # Return specific visit
            elif hn and visit_date:
                logger.debug("Returning visit by HN {} on {}.".format(hn, visit_date))

                visit = patient.visits.filter_by(date=visit_date.isoformat()).first()

                if visit:
                    return jsonify(visit)

                else:
                    abort(404)

            # How can you reach this point?
            else:
                logging.error("Unknown error.")
                abort(500)

        except (IndexError, exc.SQLAlchemyError) as e:
            logger.error("Unable to read to DB")
            logger.error(e)
            abort(500)

    def post(self, hn=None):

        if not hn:
            logger.error("No HN supplied.")
            abort(404)

        else:
            hn = hn.replace("^", "/")

        # Find the patient
        try:
            patient = Patient.query.filter_by(hn=hn).first()

            logger.debug("Recieved POST request.")
            data = self.form_data()

            # Check if the visit record exists in the db
            is_visit_exists = patient.visits.filter_by(
                date=data["date"].isoformat()
            ).scalar()

            if is_visit_exists:
                logger.debug(
                    "Visit on {} is already existed in the DB. Returning 409".format(
                        data["date"]
                    )
                )
                abort(409)

            # Record new visit
            logger.debug(
                "Adding visit on {} for patient HN {} in the DB.".format(
                    data["date"], hn
                )
            )

            new_visit = Visit(**data)
            patient.visits.append(new_visit)
            db.session.add(patient)
            db.session.commit()
            return jsonify({"status": "success"})

        except (IndexError, exc.SQLAlchemyError) as e:
            logger.error("Unable to connect to DB")
            logger.error(e)
            abort(500)

    def patch(self, hn=None, visit_date=None):
        """
        Patch visit record
        """

        logger.debug("Recieved PATCH request.")

        if not hn or not visit_date:
            logger.error(
                "No HN or Visit Date was passed along, unable to patch the record."
            )
            abort(400)

        else:
            hn = hn.replace("^", "/")

            try:
                visit_date = ISODateType(visit_date)

            except ValueError as e:
                logger.error("Invalid date supplied.")
                logger.error(e)
                abort(400)

        # Check if the patient exists in the db
        try:
            patient = Patient.query.filter_by(hn=hn).first()

            if patient is None:
                logger.error("No patient with the specified HN existed in the DB.")
                abort(404)

            # Check if the visit record exists in the db
            visit = patient.visits.filter_by(date=visit_date.isoformat()).first()

            if visit is None:
                logger.debug("Visit on {} does not exist in the DB.".format(visit_date))
                abort(400)

            logger.debug(
                "Patching a visit on {}, patient HN {}.".format(
                    visit_date.isoformat(), hn
                )
            )
            data = self.form_data()

            visit.update(**data)

            db.session.add(visit)
            db.session.commit()

            return jsonify({"status": "success"})

        except (IndexError, exc.SQLAlchemyError) as e:
            logger.error("Unable to write to DB")
            logger.error(e)
            abort(500)

    def delete(self, hn=None, visit_date=None):
        """
        Delete visit record
        """

        logger.debug("Recieved Delete request.")

        if not hn or not visit_date:
            logger.error(
                "No HN or Visit Date was passed along, unable to Delete the record."
            )
            abort(400)

        else:
            hn = hn.replace("^", "/")

            try:
                visit_date = ISODateType(visit_date)

            except ValueError as e:
                logger.error("Invalid date supplied.")
                logger.error(e)
                abort(400)

        # Check if the patient exists in the db
        try:
            patient = Patient.query.filter_by(hn=hn).first()

            if patient is None:
                logger.error("No patient with the specified HN existed in the DB.")
                abort(404)

            # Check if the visit record exists in the db
            visit = patient.visits.filter_by(date=visit_date.isoformat()).first()

            if visit is None:
                logger.debug("Visit on {} does not exist in the DB.".format(visit_date))
                abort(400)

            db.session.delete(visit)
            db.session.commit()

            return jsonify({"status": "success"})

        except (IndexError, exc.SQLAlchemyError) as e:
            logger.error("Unable to write to DB")
            logger.error(e)
            abort(500)

    def form_data(self):
        """
        Prase JSON from request
        """

        # Phrase post data
        parser = reqparse.RequestParser(trim=True)
        parser.add_argument(
            "date",
            type=lambda d: ISODateType(d),
            help="Date of Visit input field is invalid: {error_msg}",
            required=True,
        )
        parser.add_argument(
            "is_art_adherence",
            type=str,
            choices=("Yes" "No"),
            help="Art Adherence input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "art_adherence_scale",
            type=float,
            help="Art Adherence Scale input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "art_adherence_problem",
            type=str,
            help="Art Adherence Problem input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "art_delay", type=str, help="Art Delay input field is invalid: {error_msg}"
        )
        parser.add_argument(
            "hx_contact_tb",
            type=str,
            choices=("Yes" "No"),
            help="Hx of Contact TB input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "bw",
            type=float,
            help="Art Adherence Scale input field is invalid: {error_msg}",
            required=True,
        )
        parser.add_argument(
            "imp",
            action="append",
            help="Impressions input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "arv",
            action="append",
            help="ARV Regimen input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "why_switched_arv",
            action=str,
            help="Why Switched ARV? input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "oi_prophylaxis",
            action="append",
            help="OI Prophylaxis input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "anti_tb",
            action="append",
            help="Anti TB Drugs input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "vaccination",
            action="append",
            help="Vaccinations input field is invalid: {error_msg}",
        )

        # Modify list datatype to JSON
        data = parser.parse_args()

        for key in Visit.__json__:
            if data[key]:
                data[key] = json.dumps(data[key])

        return data
