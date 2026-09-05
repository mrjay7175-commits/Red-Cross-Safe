from rest_framework import serializers

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
    Branch,
    Ambulance,
    Vaccination,
    InsuranceClaim,
)


class DoctorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Doctor
        fields = "__all__"
        read_only_fields = ["doctor_id", "joining_date"]


class PatientSerializer(serializers.ModelSerializer):

    doctor_name = serializers.CharField(source="doctor.name", read_only=True)

    class Meta:
        model = Patient
        fields = "__all__"
        read_only_fields = ["patient_id", "admission_date"]


class BillSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(source="patient.name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)

    class Meta:
        model = Bill
        fields = "__all__"
        read_only_fields = ["total_amount", "bill_date"]


class MedicineSerializer(serializers.ModelSerializer):

    class Meta:
        model = Medicine
        fields = "__all__"


class AppointmentSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(source="patient.name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)

    class Meta:
        model = Appointment
        fields = "__all__"
        read_only_fields = ["created_at"]


class MedicalRecordSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(source="patient.name", read_only=True)

    class Meta:
        model = MedicalRecord
        fields = "__all__"
        read_only_fields = ["record_date"]


class LabTestSerializer(serializers.ModelSerializer):

    patient_name = serializers.CharField(source="patient.name", read_only=True)

    class Meta:
        model = LabTest
        fields = "__all__"
        read_only_fields = ["test_date"]


class WardSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ward
        fields = "__all__"


class BedSerializer(serializers.ModelSerializer):

    ward_name = serializers.CharField(source="ward.name", read_only=True)
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    is_occupied = serializers.BooleanField(read_only=True)

    class Meta:
        model = Bed
        fields = "__all__"


class AuditLogSerializer(serializers.ModelSerializer):

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = AuditLog
        fields = "__all__"
        read_only_fields = ["timestamp"]
