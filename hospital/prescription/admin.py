from django.contrib import admin
from .models import Prescription, PrescriptionItem


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):

    list_display = (
        "prescription_id",
        "patient",
        "doctor",
        "visit_date",
        "follow_up_date",
    )

    search_fields = (
        "prescription_id",
        "patient__name",
        "doctor__name",
    )

    list_filter = (
        "visit_date",
        "doctor",
    )

    inlines = [
        PrescriptionItemInline
    ]