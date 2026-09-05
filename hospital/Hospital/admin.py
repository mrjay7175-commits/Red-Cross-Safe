from django.contrib import admin
from .models import Patient, Doctor, Bill
from .models import Medicine
from .models import Appointment
from .models import MedicalRecord
from .models import LabTest, Ward, Bed, AuditLog


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "doctor",
        "status",
        "phone",
    )

    search_fields = (
        "name",
        "doctor",
        "phone",
    )


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):

    list_display = (
        "doctor_id",
        "name",
        "department",
        "phone",
        "email",
        "experience",
        "joining_date",
    )

    search_fields = (
        "doctor_id",
        "name",
        "department",
        "phone",
        "email",
    )

    list_filter = (
        "department",
        "joining_date",
    )

    ordering = (
        "doctor_id",
    )

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "patient",
        "doctor",
        "total_amount",
        "bill_date",
    )

    search_fields = (
        "patient__name",
        "doctor__name",
    )

    list_filter = (
        "bill_date",
    )

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "company",
        "category",
        "price",
        "quantity",
        "expiry_date",
    )

    search_fields = (
        "name",
        "company",
        "category",
    )

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "patient",
        "doctor",
        "appointment_date",
        "appointment_time",
        "status",
    )

    list_filter = (
        "status",
        "appointment_date",
    )

    search_fields = (
        "patient__name",
        "doctor__name",
    )

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "patient",
        "doctor",
        "diagnosis",
        "record_date",
    )

    list_filter = (
        "record_date",
    )

    search_fields = (
        "patient__name",
        "diagnosis",
    )


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "test_name", "status", "test_date")
    list_filter = ("status",)
    search_fields = ("patient__name", "test_name")


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "floor")


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ("id", "ward", "bed_number", "patient")
    list_filter = ("ward",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "action", "model_name", "object_repr", "timestamp")
    list_filter = ("action", "model_name")
    search_fields = ("object_repr",)
    readonly_fields = ("user", "action", "model_name", "object_repr", "timestamp")

    def has_add_permission(self, request):
        return False


from .models import Branch, Ambulance, Vaccination, InsuranceClaim


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "phone", "is_main")


@admin.register(Ambulance)
class AmbulanceAdmin(admin.ModelAdmin):
    list_display = ("id", "vehicle_number", "driver_name", "status", "branch")
    list_filter = ("status", "branch")


@admin.register(Vaccination)
class VaccinationAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "vaccine_name", "dose_number", "date_given")
    search_fields = ("patient__name", "vaccine_name")


@admin.register(InsuranceClaim)
class InsuranceClaimAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "insurance_provider", "claim_amount", "status")
    list_filter = ("status",)
    search_fields = ("patient__name", "insurance_provider", "policy_number")


from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "level", "created_at")
    list_filter = ("level",)
    search_fields = ("message",)
