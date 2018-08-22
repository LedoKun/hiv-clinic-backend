"""
Application Resources
Add additional RESTFUL-resources as needed
"""
from backend.app import api
from backend.resources.patient_resource import PatientResource
from backend.resources.child_resource import ChildResource


# REST reseources
api.add_resource(PatientResource, "/api/patient", "/api/patient/<string:hn>")
api.add_resource(
    ChildResource,
    "/api/patient/<string:hn>/<string:child_type>",
    "/api/patient/<string:hn>/<string:child_type>/<string:record_date>",
)
