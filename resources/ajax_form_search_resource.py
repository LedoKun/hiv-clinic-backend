from flask_restful import Resource
from backend.models import Patient, Visit, Imaging, Appointment, ICD10
from flask import jsonify, abort, request
from backend.app import app, logger
from webargs import fields
from webargs.flaskparser import parser
from flask_jwt_extended import jwt_required


class AjaxFormSearch(Resource):
    @jwt_required
    def get(self):
        # Get query info
        search_args = self.search_args()
        results = []

        logger.debug(
            "Get search request - fieldname: {}, query: {}".format(
                search_args["field_name"], search_args["query"]
            )
        )

        # ICD10 Search
        if search_args["field_name"] == "imp":
            query_results = (
                ICD10.query.search(search_args["query"], sort=True)
                .limit(app.config["MAX_SEARCH_RESULT"])
                .all()
            )

            for query_result in query_results:
                results.append(
                    "{}: {}".format(
                        query_result.icd10, query_result.description
                    )
                )

        # Patient search
        elif search_args["field_name"] == "search_bar":
            query_results = (
                Patient.query.search(search_args["query"], sort=True)
                .limit(app.config["MAX_SEARCH_RESULT"])
                .all()
            )

            for query_result in query_results:
                label = (
                    "HN #{} - {} -- Clinic ID: {}, Nationality: {}"
                    ", ID/Passport: {}, NAP: {}, Referred From: {}"
                ).format(
                    query_result.hn,
                    query_result.name,
                    query_result.hiv_clinic_id,
                    query_result.nationality,
                    query_result.gov_id,
                    query_result.nap,
                    query_result.refer_from,
                )
                results.append({"label": label, "hn": query_result.hn})

        else:
            model = None
            column = None

            if search_args["field_name"] == "refer_from":
                model = Patient

            elif search_args["field_name"] in [
                "art_adherence_problem",
                "why_switched_arv",
            ]:
                model = Visit

            elif search_args["field_name"] in ["film_type", "result"]:
                model = Imaging

            elif search_args["field_name"] in ["appointment_for"]:
                model = Appointment

            else:
                logger.error("Invalid field name.")
                abort(409)

            column = getattr(model, search_args["field_name"])
            distinct_results = (
                model.query.filter(
                    column.ilike("%{}%".format(search_args["query"]))
                )
                .distinct()
                .limit(app.config["MAX_SEARCH_RESULT"])
                .all()
            )

            for distinct_result in distinct_results:
                results.append(
                    getattr(distinct_result, search_args["field_name"])
                )

        return jsonify(results)

    def search_args(self):
        args = {
            "field_name": fields.String(required=True),
            "query": fields.String(required=True),
        }

        # Phrase args data
        data = parser.parse(args, request)
        return data
