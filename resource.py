"""
Application Resources
Add additional RESTFUL-resources as needed
"""
from backend.app import api
from backend.resources.patient_resource import PatientResource
from backend.resources.visit_resource import VisitResource


# REST reseources
api.add_resource(PatientResource, "/api/patient", "/api/patient/<string:hn>")
api.add_resource(
    VisitResource,
    "/api/patient/<string:hn>/visit",
    "/api/patient/<string:hn>/visit/<string:visit_date>",
)
