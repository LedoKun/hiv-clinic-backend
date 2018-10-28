"""
Application Resources
Add additional RESTFUL-resources as needed
"""
from backend.app import api

# Resources
from backend.resources.patient_resource import PatientResource
from backend.resources.child_resource import ChildResource
from backend.resources.is_existed_resource import IsExistedResource
from backend.resources.appointment_resource import AppointmentResource
from backend.resources.stats_resource import StatsResource
from backend.resources.login_resource import LoginResource
from backend.resources.logout_resource import LogoutResource
from backend.resources.ajax_form_search_resource import AjaxFormSearch

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
api.add_resource(LoginResource, "/api/login")
api.add_resource(LogoutResource, "/api/logout")
