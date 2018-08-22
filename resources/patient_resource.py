from flask_restful import Resource, reqparse
from backend.models import Patient
from flask import jsonify, abort
from backend.app import db, logger
from sqlalchemy import func
from backend.common.form_types import ISODateType
from sqlalchemy import exc
import json


class PatientResource(Resource):
    def get(self, hn=None):
        """
        Return GET request for patient HN
        """

        if not hn:
            no_of_patients = db.session.query(func.count(Patient.id)).scalar()
            logger.debug(
                "Return all total number of patient - {}".format(no_of_patients)
            )
            return jsonify({"no_of_patients": no_of_patients})

        else:
            hn = hn.replace("^", "/")

        patient = Patient.query.filter_by(hn=hn).first()

        if patient is None:
            logger.error("HN {} does not exist in the database.".format(hn))
            abort(404)

        else:
            logger.info("Return information for HN {}.".format(hn))
            return jsonify({"patient_data": patient})

    def post(self, hn=None):
        """
        Create new patient
        """

        logger.debug("Recieved POST request.")
        data = self.form_data()

        # Check if the patient exists in the db
        is_patient_exists = Patient.is_exists(col=Patient.hn, str_filter=data["hn"])

        if is_patient_exists:
            logger.debug(
                "HN {} is already existed in the DB. Returning 409".format(data["hn"])
            )
            abort(409)

        logger.debug("Adding patient HN {} in the DB.".format(data["hn"]))

        try:
            patient = Patient(**data)
            db.session.add(patient)
            db.session.commit()
            return jsonify({"status": "success"})

        except (IndexError, exc.SQLAlchemyError) as e:
            logger.error("Unable to write to DB")
            logger.error(e)
            abort(500)

    def patch(self, hn=None):
        """
        Update patient information
        """

        logger.debug("Recieved PATCH request.")

        if not hn:
            logger.error("No HN was passed along, unable to PATCH the record.")
            abort(400)

        else:
            hn = hn.replace("^", "/")

        data = self.form_data()

        if data["hn"] != hn:
            logger.error("HN from PATCH request and JSON data are not equal.")
            abort(400)

        # Check if the patient exists in the db
        is_patient_exists = Patient.is_exists(col=Patient.hn, str_filter=data["hn"])

        if not is_patient_exists:
            logger.error("No patient with the specified HN existed in the DB.")
            abort(404)

        logger.debug("Patching patient HN {} in the DB.".format(data["hn"]))

        try:
            patient = Patient.query.filter_by(hn=data["hn"]).first()
            patient.update(**data)
            db.session.add(patient)
            db.session.commit()

            return jsonify({"status": "success"})

        except (IndexError, exc.SQLAlchemyError) as e:
            logger.error("Unable to write to DB")
            logger.error(e)
            abort(500)

    # Do soft delete/delete children?
    def delete(self, hn=None):
        """
        Delete patient record
        """

        logger.debug("Recieved Delete request.")

        if not hn:
            logger.error("No HN was passed along, unable to Delete the record.")
            abort(400)

        else:
            hn = hn.replace("^", "/")

        try:
            # Check if the patient exists in the db
            patient = Patient.query.filter_by(hn=hn)
            # is_patient_exists = Patient.is_exists(col=Patient.hn, str_filter=hn)

            if patient is None:
                logger.error("No patient with the specified HN existed in the DB.")
                abort(404)

            # patient.children.remove(visits, labs, imaging, appointments)
            db.session.delete(patient)
            # db.session.query(Patient).filter(Patient.hn == hn).delete()
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
            "gov_id_type",
            type=str,
            choices=("บัตรประชาชน", "พาสปอร์ต"),
            help="Government ID Type input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "gov_id", type=str, help="Government ID input field is invalid: {error_msg}"
        )
        parser.add_argument(
            "name",
            type=str,
            help="Name input field is invalid: {error_msg}",
            required=True,
        )
        parser.add_argument(
            "dob",
            type=lambda d: ISODateType(d),
            help="Date of Birth input field is invalid: {error_msg}",
            required=True,
        )
        parser.add_argument(
            "first_encounter",
            type=lambda d: ISODateType(d),
            help="First Encounter Date input field is invalid: {error_msg}",
            required=True,
        )
        parser.add_argument(
            "sex",
            type=str,
            choices=("ชาย", "หญิง"),
            help="Sex input field is invalid: {error_msg}",
            required=True,
        )
        parser.add_argument(
            "gender",
            type=str,
            choices=("Male", "Female", "MSM", "Bisexual", "Lesbian", "TG"),
            help="Gender input field is invalid: {error_msg}",
            required=True,
        )
        parser.add_argument(
            "marital",
            type=str,
            choices=("โสด", "สมรส", "หย่าร้าง", "ม่าย"),
            help="Marital Status input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "nationality",
            type=str,
            help="Nationality input field is invalid: {error_msg}",
            required=True,
        )
        parser.add_argument(
            "education",
            type=str,
            choices=(
                "ต่ำกว่ามัธยมศึกษาตอนปลาย",
                "มัธยมศึกษาตอนปลาย",
                "ปวช/ปวส",
                "ปริญญาตรี",
                "ปริญญาโท",
                "ปริญญาเอก",
            ),
            help="Education input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "address", type=str, help="address input field is invalid: {error_msg}"
        )
        parser.add_argument(
            "tel",
            action="append",
            help="Telephone Number input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "relative_tel",
            action="append",
            help="Relative Telephone Number input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "is_refer",
            type=str,
            choices=(
                "ผู้ป่วยใหม่",
                "ผู้ป่วยรับโอน (ยังไม่เริ่มยา ARV)",
                "ผู้ป่วยรับโอน (เริ่มยา ARV แล้ว)",
            ),
            help="Referral Status input field is invalid: {error_msg}",
            required=True,
        )
        parser.add_argument(
            "refer_from",
            type=str,
            help="Refer From input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "hn", type=str, help="HN input field is invalid: {error_msg}", required=True
        )
        parser.add_argument(
            "hiv_clinic_id",
            type=str,
            help="Clinic ID input field is invalid: {error_msg}",
        )
        parser.add_argument(
            "nap", type=str, help="NAP ID input field is invalid: {error_msg}"
        )
        parser.add_argument(
            "bill_payer",
            type=str,
            choices=(
                "ประกันสุขภาพทั่วหน้า",
                "ประกันสุขภาพทั่วหน้า นอกเขต",
                "ประกันสังคม",
                "ประกันสังคม ต่างรพ.",
                "ข้าราชการ/จ่ายตรง",
                "ต่างด้าว",
                "ชำระเงิน",
            ),
            help="Bill Payer input field is invalid: {error_msg}",
            required=True,
        )
        parser.add_argument(
            "plan", action="append", help="Plan input field is invalid: {error_msg}"
        )

        # Modify list datatype to JSON
        data = parser.parse_args()
        data = Patient.convert_to_json(data)

        return data
