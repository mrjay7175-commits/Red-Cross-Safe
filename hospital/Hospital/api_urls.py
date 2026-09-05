from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from .api_views import (
    PatientViewSet,
    DoctorViewSet,
    BillViewSet,
    MedicineViewSet,
    AppointmentViewSet,
    MedicalRecordViewSet,
    LabTestViewSet,
    WardViewSet,
    BedViewSet,
    AuditLogViewSet,
)

router = DefaultRouter()
router.register("patients", PatientViewSet, basename="api-patients")
router.register("doctors", DoctorViewSet, basename="api-doctors")
router.register("bills", BillViewSet, basename="api-bills")
router.register("medicines", MedicineViewSet, basename="api-medicines")
router.register("appointments", AppointmentViewSet, basename="api-appointments")
router.register("medical-records", MedicalRecordViewSet, basename="api-medical-records")
router.register("lab-tests", LabTestViewSet, basename="api-lab-tests")
router.register("wards", WardViewSet, basename="api-wards")
router.register("beds", BedViewSet, basename="api-beds")
router.register("audit-logs", AuditLogViewSet, basename="api-audit-logs")

urlpatterns = [
    # POST username/password here to get an auth token for API requests
    path("auth-token/", obtain_auth_token, name="api_auth_token"),
    path("", include(router.urls)),
]
