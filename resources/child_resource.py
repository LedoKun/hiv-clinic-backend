from flask_restful import Resource, reqparse
from flask import jsonify, abort
from backend.app import db, logger
from backend.common.form_types import ISODateType
from sqlalchemy import exc, exists
from sqlalchemy.orm import load_only
from backend.models import Patient, Visit, Lab, Imaging, Appointment
import json


class ChildResource(Resource):
    def get(self, hn=None, child_type=None, record_date=None):

        # Change HN and record_date format
        if not hn or not child_type in Patient.__children__:
            logger.error(
                "No valid HN {} or child type {} supplied.".format(hn, child_type)
            )
            abort(404)

        else:
            hn = hn.replace("^", "/")

        if record_date:
            try:
                record_date = ISODateType(record_date)

            except ValueError as e:
                logger.error("Invalid date format supplied ({}).".format(record_date))
                logger.error(e)
                abort(400)

        # Read from DB
        try:
            patient = Patient.query.filter_by(hn=hn).first()

            if not patient:
                logger.error("No patient HN {} with {} found.".format(hn, child_type))
                abort(404)

            # Return all children
            if hn and not record_date:
                logger.debug("Returning all {} by HN {}.".format(child_type, hn))

                children = getattr(patient, child_type).all()
                return jsonify(children)

            # Return specific child
            elif hn and record_date:
                logger.debug(
                    "Returning a row from child table by HN {} on {}.".format(
                        hn, record_date
                    )
                )

                child = (
                    getattr(patient, child_type)
                    .filter_by(date=record_date.isoformat())
                    .first()
                )
                if child:
                    return jsonify(child)

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

    def post(self, hn=None, child_type=None, record_date=None):

        if not hn or not child_type in Patient.__children__:
            logger.error(
                "No valid HN {} or child type {} supplied.".format(hn, child_type)
            )
            abort(404)

        else:
            hn = hn.replace("^", "/")

        # Find the patient
        try:
            patient = Patient.query.filter_by(hn=hn).first()

            if patient is None:
                logger.error("No patient with the specified HN existed in the DB.")
                abort(404)

            logger.debug("Recieved POST request for child {}, patient HN {}.".format(child_type, hn))

            # Form data validation
            data = {}
            new_record = None

            if child_type == "visits":
                data = self.visit_form_data()
                new_record = Visit(**data)

            elif child_type == "labs":
                data = self.lab_form_data()
                new_record = Lab(**data)

            elif child_type == "imaging":
                data = self.imaging_form_data()  # Todo
                new_record = Imaging(**data)

            elif child_type == "appointments":
                data = self.appointment_form_data()  # Todo
                new_record = Appointment(**data)

            else:
                logger.error("Undefined child type {}.".format(child_type))
                abort(404)

            # Check if the record exists in the db
            child_column = getattr(patient, child_type)
            is_exists = child_column.filter_by(date=data["date"].isoformat()).scalar()

            if is_exists:
                logger.debug(
                    "Record for {} on {} is already existed in the DB. Returning 409".format(
                        child_type, data["date"]
                    )
                )
                abort(409)

            # Add a new record
            logger.debug(
                "Adding record for {} on {} for patient HN {} in the DB.".format(
                    child_type, data["date"], hn
                )
            )

            child_column.append(new_record)
            db.session.add(patient)
            db.session.commit()

            return jsonify({"status": "success"})

        except (IndexError, exc.SQLAlchemyError) as e:
            logger.error("Unable to connect to DB")
            logger.error(e)
            abort(500)

    def patch(self, hn=None, child_type=None, record_date=None):
        """
        Patch visit record
        """

        logger.debug("Recieved PATCH request.")

        if not hn or not record_date or not child_type in Patient.__children__:
            logger.error(
                "No HN or Visit Date or data type was passed along, unable to patch the record."
            )
            abort(400)

        else:
            hn = hn.replace("^", "/")

            try:
                record_date = ISODateType(record_date)

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

            # Check if the record exists in the db
            child_column = getattr(patient, child_type)
            record = child_column.filter_by(date=record_date.isoformat()).first()

            if not record:
                logger.debug("Record type {} on {} does not exist in the DB.".format(child_type, record_date))
                abort(400)

            logger.debug(
                "Patching a {} record on {}, patient HN {}.".format(
                    child_type, record_date.isoformat(), hn
                )
            )

            # Form data validation
            data = {}

            if child_type == "visits":
                data = self.visit_form_data()

            elif child_type == "labs":
                data = self.lab_form_data()

            elif child_type == "imaging":
                data = self.imaging_form_data()

            elif child_type == "appointments":
                data = self.appointment_form_data()

            else:
                logger.error("Undefined child type {}.".format(child_type))
                abort(404)

            record.update(**data)
            db.session.add(record)
            db.session.commit()

            return jsonify({"status": "success"})

        except (IndexError, exc.SQLAlchemyError) as e:
            logger.error("Unable to write to DB")
            logger.error(e)
            abort(500)

    def delete(self, hn=None, child_type=None, record_date=None):
        """
        Delete visit record
        """

        logger.debug("Recieved Delete request.")

        if not hn or not record_date or not child_type in Patient.__children__:
            logger.error(
                "No HN or Record Date or Child Type was passed along, unable to Delete the record."
            )
            abort(400)

        else:
            hn = hn.replace("^", "/")

            try:
                record_date = ISODateType(record_date)

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

            # Check if the record exists in the db
            child_column = getattr(patient, child_type)
            record = child_column.filter_by(date=record_date.isoformat()).first()

            if record is None:
                logger.debug("Record on {} does not exist in the DB.".format(record_date))
                abort(400)

            db.session.delete(record)
            db.session.commit()

            return jsonify({"status": "success"})

        except (IndexError, exc.SQLAlchemyError) as e:
            logger.error("Unable to write to DB")
            logger.error(e)
            abort(500)

    def visit_form_data(self):
        """
        Prase JSON from request
        """

        # Phrase post data
        parser = reqparse.RequestParser(trim=True)
        parser.add_argument(
            "date",
            type=lambda d: ISODateType(d),
            help="Date input field is invalid: {error_msg}",
            required=True,
        )
        parser.add_argument(
            "is_art_adherence",
            type=str,
            choices=("Yes", "No"),
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
            choices=("Yes", "No"),
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
        data = Visit.convert_to_json(data)

        return data

    def lab_form_data(self):
        """
        Prase JSON from request
        """

        # Phrase post data
        parser = reqparse.RequestParser(trim=True)
        parser.add_argument(
            "date",
            type=lambda d: ISODateType(d),
            help="Date input field is invalid: {error_msg}",
            required=True,
        )
        parser.add_argument(
            "anti_hiv",
            type=str,
            choices=("+", "-", "+/-"),
            help="Anti HIV input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "cd4", type=int, help="CD4 input field is invalid: {error_msg}"
        )
        parser.add_argument(
            "p_cd4", type=float, help="Percent CD4 input field is invalid: {error_msg}"
        )
        parser.add_argument(
            "vl", type=str, help="Viral Load input field is invalid: {error_msg}"
        )

        parser.add_argument(
            "hiv_resistence",
            type=str,
            help="HIV Resistence input field is invalid: {error_msg}",
        )

        parser.add_argument(
            "hbsag",
            type=str,
            choices=("+", "-", "+/-"),
            help="HBsAg input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "anti_hbs",
            type=str,
            choices=("+", "-", "+/-"),
            help="Anti-HBs input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "anti_hcv",
            type=str,
            choices=("+", "-", "+/-"),
            help="Anti-HCV input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "afb",
            type=str,
            choices=("3+", "2+", "1+", "Scantly", "-"),
            help="AFB input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "sputum_cs",
            type=str,
            choices=("+", "-", "+/-"),
            help="Sputum Culture input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "genexpert",
            type=str,
            choices=("MTB +", "MTB With RIF Resistance +" "MTB -"),
            help="GeneXpert input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "vdrl",
            type=str,
            choices=("+", "-", "+/-"),
            help="VDRL input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "rpr", type=str, help="RPR Titer input field is invalid: {error_msg}"
        )

        # Modify list datatype to JSON
        data = parser.parse_args()
        data = Lab.convert_to_json(data)

        return data

    def imaging_form_data(self):
        """
        Prase JSON from request
        """

        # Phrase post data
        parser = reqparse.RequestParser(trim=True)
        parser.add_argument(
            "date",
            type=lambda d: ISODateType(d),
            help="Date input field is invalid: {error_msg}",
            required=True
        )
        parser.add_argument(
            "film_type",
            type=str,
            help="Film Type input field is invalid: {error_msg}",
            required=True
        )
        parser.add_argument(
            "result",
            type=str,
            help="Imaging Result input field is invalid: {error_msg}",
            required=True
        )

        # Modify list datatype to JSON
        data = parser.parse_args()
        data = Imaging.convert_to_json(data)
        return data

    def appointment_form_data(self):
        """
        Prase JSON from request
        """

        # Phrase post data
        parser = reqparse.RequestParser(trim=True)
        parser.add_argument(
            "date",
            type=lambda d: ISODateType(d),
            help="Date input field is invalid: {error_msg}",
            required=True,
        )
        parser.add_argument(
            "appointment_for",
            type=str,
            help="Appointment plan input field is invalid: {error_msg}",
        )

        # Modify list datatype to JSON
        data = parser.parse_args()
        data = Appointment.convert_to_json(data)
        return data

# TODO: Improve sqlalchemy query!
# Look at https://stackoverflow.com/questions/12593421/sqlalchemy-and-flask-how-to-query-many-to-many-relationship
# And use join like https://stackoverflow.com/questions/37013491/flask-sqlalchemy-relationship-query
