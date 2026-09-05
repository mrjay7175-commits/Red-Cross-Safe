from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Patient,
    Doctor,
    Bill,
    Medicine,
    Appointment,
    MedicalRecord,
    LabTest,
    Ward,
    Bed,
    AuditLog,
)

from .serializers import (
    PatientSerializer,
    DoctorSerializer,
    BillSerializer,
    MedicineSerializer,
    AppointmentSerializer,
    MedicalRecordSerializer,
    LabTestSerializer,
    WardSerializer,
    BedSerializer,
    AuditLogSerializer,
)


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by("-id")
    serializer_class = PatientSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["status", "gender", "doctor"]
    search_fields = ["name", "disease", "patient_id"]


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all().order_by("-id")
    serializer_class = DoctorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["department", "gender"]
    search_fields = ["name", "department", "doctor_id"]


class BillViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all().order_by("-id")
    serializer_class = BillSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["patient", "doctor"]


class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all().order_by("-id")
    serializer_class = MedicineSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["category", "company"]
    search_fields = ["name", "company", "category"]


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all().order_by("-id")
    serializer_class = AppointmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "patient", "doctor", "appointment_date"]


class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.all().order_by("-record_date")
    serializer_class = MedicalRecordSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["patient", "doctor"]


class LabTestViewSet(viewsets.ModelViewSet):
    queryset = LabTest.objects.all().order_by("-test_date")
    serializer_class = LabTestSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["patient", "doctor", "status"]


class WardViewSet(viewsets.ModelViewSet):
    queryset = Ward.objects.all().order_by("name")
    serializer_class = WardSerializer


class BedViewSet(viewsets.ModelViewSet):
    queryset = Bed.objects.all().order_by("ward", "bed_number")
    serializer_class = BedSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["ward", "patient"]


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by("-timestamp")
    serializer_class = AuditLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["action", "model_name", "user"]
