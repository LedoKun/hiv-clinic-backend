"""
Application Resources
Add additional RESTFUL-resources as needed
"""
from backend.app import api
from backend.resources.patient_resource import PatientResource
from backend.resources.child_resource import ChildResource
from backend.resources.is_existed_resource import IsExistedResource
from backend.resources.ajax_form_search import AjaxFormSearch
from backend.resources.appointment import AppointmentResource
from backend.resources.stats import StatsResource

# REST reseources
api.add_resource(PatientResource, "/api/patient", "/api/patient/<string:hn>")
api.add_resource(
    ChildResource,
    "/api/patient/<string:hn>/<string:child_type>",
    "/api/patient/<string:hn>/<string:child_type>/<string:record_id>",
)
api.add_resource(IsExistedResource, "/api/search/is_existed")
api.add_resource(AjaxFormSearch, "/api/search/field_entries")
api.add_resource(AppointmentResource, "/api/appointment")
api.add_resource(StatsResource, "/api/stats")
