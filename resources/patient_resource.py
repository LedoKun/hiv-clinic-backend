from flask_restful import Resource
from backend.models import Patient
from flask import jsonify, abort, request
from backend.app import db, logger
from sqlalchemy import func, exc
import json
from webargs import fields
from marshmallow import validate, ValidationError
from webargs.flaskparser import parser


class PatientResource(Resource):
    def get(self, hn=None):
        """
        Return GET request for patient HN
        """

        if not hn:
            no_of_patients = db.session.query(func.count(Patient.id)).scalar()
            logger.debug(
                "Returning total number of patients: {}.".format(no_of_patients)
            )
            return jsonify({"result": no_of_patients})

        else:
            hn = hn.replace("^", "/")

        patient = Patient.query.filter_by(hn=hn).first()

        if patient is None:
            logger.error("HN {} not found.".format(hn))
            abort(404)

        else:
            logger.info("Found HN {}.".format(hn))
            return jsonify(patient)

    def post(self, hn=None):
        """
        Create new patient
        """

        logger.debug("Recieved POST request.")
        data = self.form_data()

        # Check if the patient exists in db
        is_patient_exists = Patient.is_exists(col=Patient.hn, str_filter=data["hn"])

        if is_patient_exists:
            logger.debug("HN {} existed in DB.".format(data["hn"]))
            abort(409)

        # Check for uniqueness
        for col in Patient.__unique__:
            try:
                if not col in data:
                    continue

                column = getattr(Patient, col)
                is_exists = Patient.is_exists(col=column, str_filter=data[col])

                if is_exists:
                    logger.warn("Submitted data failed the uniqueness test.")
                    abort(409)

            except (IndexError, KeyError, exc.SQLAlchemyError) as e:
                logger.debug(e)

        try:
            logger.debug("Saving HN {} in DB.".format(data["hn"]))

            patient = Patient(**data)
            db.session.add(patient)
            db.session.commit()
            return jsonify({"result": "success"})

        except (IndexError, exc.SQLAlchemyError) as e:
            logger.error("Unable to commit to DB.")
            logger.error(e)
            abort(500)

    def patch(self, hn=None):
        """
        Update patient information
        """

        logger.debug("Recieved PATCH request.")

        if not hn:
            logger.error("No HN information.")
            abort(400)

        else:
            hn = hn.replace("^", "/")

        data = self.form_data()

        if data["hn"] != hn:
            logger.error("Recieved two different HNs.")
            abort(409)

        # Check if the patient exists in the db
        is_patient_exists = Patient.is_exists(col=Patient.hn, str_filter=data["hn"])

        if not is_patient_exists:
            logger.error("HN {} not found in DB".format(data["hn"]))
            abort(404)

        # Check for uniqueness
        for col in Patient.__unique__:
            try:
                column = getattr(Patient, col)
                is_exists = (
                    Patient.query.with_entities(Patient.hn)
                    .filter(column == data[col])
                    .filter(Patient.hn != data["hn"])
                    .scalar()
                )

                if is_exists:
                    logger.debug(
                        "str_filter: {} existed in column: {}.".format(data[col]), col
                    )
                    abort(409)

            except (IndexError, KeyError, exc.SQLAlchemyError):
                pass

        try:
            logger.debug("Patiching HN {} in DB.".format(data["hn"]))

            patient = Patient.query.filter_by(hn=data["hn"]).first()
            patient.update(**data)
            db.session.add(patient)
            db.session.commit()

            return jsonify({"result": "success"})

        except (IndexError, exc.SQLAlchemyError, exc.IntegrityError) as e:
            logger.error("Unable to commit to DB.")
            logger.error(e)
            abort(500)

    def delete(self, hn=None):
        """
        Delete patient record
        """

        logger.debug("Recieved Delete request.")

        if not hn:
            logger.error("No HN information.")
            abort(400)

        else:
            hn = hn.replace("^", "/")

        try:
            # Check if the patient exists in the db
            patient = Patient.query.filter_by(hn=hn)
            # is_patient_exists = Patient.is_exists(col=Patient.hn, str_filter=hn)

            if patient is None:
                logger.error("HN {} not found in DB".format(data["hn"]))
                abort(404)

            # patient.children.remove(visits, labs, imaging, appointments)
            db.session.delete(patient)
            # db.session.query(Patient).filter(Patient.hn == hn).delete()
            db.session.commit()

            return jsonify({"result": "success"})

        except (IndexError, exc.SQLAlchemyError, exc.IntegrityError) as e:
            logger.error("Unable to commit to DB.")
            logger.error(e)
            abort(500)

    def form_data(self):
        """
        Prase JSON from request
        """

        # JSON Schema
        json_args = {
            "gov_id_type": fields.String(
                validate=validate.OneOf(["บัตรประชาชน", "พาสปอร์ต"])
            ),
            "gov_id": fields.String(),
            "name": fields.String(required=True),
            "dob": fields.Date(),
            "first_encounter": fields.Date(),
            "sex": fields.String(
                validate=validate.OneOf(["ชาย", "หญิง"]), required=True
            ),
            "gender": fields.String(
                validate=validate.OneOf(
                    ["Male", "Female", "MSM", "Bisexual", "Lesbian", "TG"]
                ),
                required=True,
            ),
            "marital": fields.String(
                validate.OneOf(["โสด", "สมรส", "หย่าร้าง", "ม่าย"])
            ),
            "nationality": fields.String(required=True),
            "education": fields.String(
                validate=validate.OneOf(
                    [
                        "ต่ำกว่ามัธยมศึกษาตอนปลาย",
                        "มัธยมศึกษาตอนปลาย",
                        "ปวช/ปวส",
                        "ปริญญาตรี",
                        "ปริญญาโท",
                        "ปริญญาเอก",
                    ]
                )
            ),
            "address": fields.String(),
            "tel": fields.List(fields.String(allow_missing=True)),
            "relative_tel": fields.List(fields.String(allow_missing=True)),
            "is_refer": fields.String(
                required=True,
                validate=validate.OneOf(
                    [
                        "ผู้ป่วยใหม่",
                        "ผู้ป่วยรับโอน (ยังไม่เริ่ม ARV)",
                        "ผู้ป่วยรับโอน (เริ่ม ARV แล้ว)",
                    ]
                ),
            ),
            "refer_from": fields.String(),
            "hn": fields.String(required=True),
            "hiv_clinic_id": fields.String(),
            "nap": fields.String(),
            "bill_payer": fields.String(
                required=True,
                validate=validate.OneOf(
                    [
                        "ประกันสุขภาพทั่วหน้า",
                        "ประกันสุขภาพทั่วหน้า นอกเขต",
                        "ประกันสังคม",
                        "ประกันสังคม ต่างรพ.",
                        "ข้าราชการ/จ่ายตรง",
                        "ต่างด้าว",
                        "ชำระเงิน",
                    ]
                ),
            ),
            "plans": fields.List(
                fields.Nested(
                    {
                        "date": fields.Date(required=True),
                        "plan": fields.String(required=True),
                    },
                    allow_missing=True,
                )
            ),
        }

        # Phrase post data
        data = parser.parse(json_args, request, locations=["json"])

        # Modify list datatype to JSON
        data = Patient.convert_to_json(data)

        return data
