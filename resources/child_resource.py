from flask_restful import Resource
from flask import jsonify, abort, request
from backend.app import db, logger, app
from sqlalchemy import exc
from backend.models import Patient, Visit, Lab, Imaging, Appointment
from webargs import fields
from marshmallow import validate
from webargs.flaskparser import parser
from flask_jwt_extended import jwt_required


class ChildResource(Resource):
    @jwt_required
    def get(self, hn=None, child_type=None, record_id=None):

        # Change HN format
        if not hn or child_type not in Patient.__children__:
            logger.error(
                "Either resource type or patient HN is not supplied.".format(
                    hn, child_type
                )
            )
            abort(404)

        else:
            hn = hn.replace("^", "/")

        # Read from DB
        try:
            patient = Patient.query.filter_by(hn=hn).first()

            if not patient:
                logger.error(
                    "Child: {}, HN: {}, not found.".format(hn, child_type)
                )
                abort(404)

            # Return all children
            if hn and not record_id:
                page = request.args.get("page", default=1, type=int)
                logger.debug(
                    "Returning HN {} {}; page {}.".format(hn, child_type, page)
                )

                childrenPaginate = getattr(patient, child_type).paginate(
                    page=page, per_page=app.config["MAX_PAGINATION"]
                )

                return jsonify(
                    {
                        "items": childrenPaginate.items,
                        "page": childrenPaginate.page,
                        "pages": childrenPaginate.pages,
                        "total": childrenPaginate.total,
                        "perPage": app.config["MAX_PAGINATION"],
                    }
                )

            # Return specific child
            elif hn and record_id:
                logger.debug(
                    "Returning a row from: {}, HN: {} on {}.".format(
                        child_type, hn, record_id
                    )
                )

                child = (
                    getattr(patient, child_type)
                    .filter_by(id=record_id)
                    .first()
                )

                if child:
                    return jsonify(child)

                else:
                    abort(404)

            # How can you reach this point?
            else:
                logger.error("Unknown error.")
                abort(500)

        except (IndexError, exc.SQLAlchemyError) as e:
            logger.error("Unable to read to DB")
            logger.error(e)
            abort(500)

    @jwt_required
    def put(self, hn=None, child_type=None, record_id=None):

        if not hn or child_type not in Patient.__children__:
            logger.error(
                "No valid HN {} or child type {} supplied.".format(
                    hn, child_type
                )
            )
            abort(404)

        else:
            hn = hn.replace("^", "/")

        if record_id:
            try:
                record_id = int(record_id)

            except ValueError:
                record_id = None

        try:
            # Find HN
            patient = Patient.query.filter(Patient.hn == hn).first()

            if not patient:
                logger.error("HN {} not found .".format(hn))
                abort(404)

            # Find if there is a record
            child_column = getattr(patient, child_type)

            if record_id:
                record = child_column.filter_by(id=record_id).first()

            else:
                record = None

            if record:
                # Update the value
                data = {}

                # Form data validation
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

                logger.debug(
                    "Patching a {} record ID {}, patient HN {}.".format(
                        child_type, record_id, hn
                    )
                )

                import sys

                print(data["date"], file=sys.stdout)

                record.update(**data)
                db.session.add(record)
                db.session.commit()

                return jsonify({"status": "success"})

            else:
                # Add new value
                child_column = getattr(patient, child_type)
                data = {}
                new_record = None

                # Form data validation
                if child_type == "visits":
                    data = self.visit_form_data()
                    new_record = Visit(**data)

                elif child_type == "labs":
                    data = self.lab_form_data()
                    new_record = Lab(**data)

                elif child_type == "imaging":
                    data = self.imaging_form_data()
                    new_record = Imaging(**data)

                elif child_type == "appointments":
                    data = self.appointment_form_data()
                    new_record = Appointment(**data)

                else:
                    logger.error("Undefined child type {}.".format(child_type))
                    abort(404)

                # Add a new record
                logger.debug(
                    (
                        "Adding record for {} on {} "
                        "for patient HN {} in the DB."
                    ).format(child_type, data["date"], hn)
                )

                child_column.append(new_record)
                db.session.add(patient)
                db.session.commit()

                return jsonify({"status": "success"})

        except (IndexError, exc.SQLAlchemyError) as e:
            logger.error("Unable to connect to DB")
            logger.error(e)
            abort(500)

    @jwt_required
    def delete(self, hn=None, child_type=None, record_id=None):
        """
        Delete visit record
        """

        logger.debug("Recieved Delete request.")

        if not hn or not record_id or child_type not in Patient.__children__:
            logger.error(
                (
                    "No HN or Record Date or Child "
                    "Type was passed along, unable to Delete the record."
                )
            )
            abort(400)

        else:
            hn = hn.replace("^", "/")

        # Check if the patient exists in the db
        try:
            patient = Patient.query.filter_by(hn=hn).first()

            if patient is None:
                logger.error(
                    "No patient with the specified HN existed in the DB."
                )
                abort(404)

            # Check if the record exists in the db
            child_column = getattr(patient, child_type)
            record = child_column.filter_by(id=record_id).first()

            if record is None:
                logger.debug(
                    "Record on {} does not exist in the DB.".format(record_id)
                )
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

        # JSON Schema
        json_args = {
            "date": fields.Date(required=True),
            "is_art_adherence": fields.String(
                validate=validate.OneOf(["Yes", "No"])
            ),
            "art_delay": fields.Float(),
            "art_adherence_scale": fields.Float(),
            "art_adherence_problem": fields.String(),
            "hx_contact_tb": fields.String(),
            "bw": fields.Float(),
            "abn_pe": fields.List(fields.String(allow_missing=True)),
            "imp": fields.List(
                fields.String(), validate=validate.Length(min=1)
            ),
            "arv": fields.List(fields.String(allow_missing=True)),
            "why_switched_arv": fields.String(),
            "oi_prophylaxis": fields.List(fields.String(allow_missing=True)),
            "anti_tb": fields.List(fields.String(allow_missing=True)),
            "vaccination": fields.List(fields.String(allow_missing=True)),
        }

        # Phrase post data
        data = parser.parse(json_args, request, locations=["json"])

        # Modify list datatype to JSON
        data = Visit.convert_to_json(data)

        return data

    def lab_form_data(self):
        """
        Prase JSON from request
        """

        # JSON Schema
        json_args = {
            "date": fields.Date(required=True),
            "anti_hiv": fields.String(
                validate=validate.OneOf(["+", "-", "+/-"])
            ),
            "cd4": fields.Integer(),
            "p_cd4": fields.Float(),
            "vl": fields.Integer(),
            "hiv_resistence": fields.String(),
            "hbsag": fields.String(validate=validate.OneOf(["+", "-", "+/-"])),
            "anti_hbs": fields.String(
                validate=validate.OneOf(["+", "-", "+/-"])
            ),
            "anti_hcv": fields.String(
                validate=validate.OneOf(["+", "-", "+/-"])
            ),
            "afb": fields.String(
                validate=validate.OneOf(["3+", "2+", "1+", "Scantly", "-"])
            ),
            "sputum_gs": fields.String(),
            "sputum_cs": fields.String(),
            "genexpert": fields.String(),
            "vdrl": fields.String(validate=validate.OneOf(["+", "-", "+/-"])),
            "rpr": fields.String(validate=validate.Regexp(r"^1:\d+$")),
        }

        # Phrase post data
        data = parser.parse(json_args, request, locations=["json"])

        # Modify list datatype to JSON
        data = Lab.convert_to_json(data)

        return data

    def imaging_form_data(self):
        """
        Prase JSON from request
        """

        # JSON Schema
        json_args = {
            "date": fields.Date(required=True),
            "film_type": fields.String(required=True),
            "result": fields.String(required=True),
        }

        # Phrase post data
        data = parser.parse(json_args, request, locations=["json"])

        # Modify list datatype to JSON
        data = Imaging.convert_to_json(data)

        return data

    def appointment_form_data(self):
        """
        Prase JSON from request
        """

        # JSON Schema
        json_args = {
            "date": fields.Date(required=True),
            "appointment_for": fields.String(required=True),
        }

        # Phrase post data
        data = parser.parse(json_args, request, locations=["json"])

        # Modify list datatype to JSON
        data = Appointment.convert_to_json(data)

        return data
