from django.db import models
from django.db.models import Max
from Hospital.models import Patient, Doctor, Medicine


class Prescription(models.Model):

    prescription_id = models.CharField(
        max_length=12,
        unique=True,
        editable=False,
        blank=True
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )

    visit_date = models.DateField(auto_now_add=True)

    diagnosis = models.TextField()

    symptoms = models.TextField(
        blank=True,
        null=True
    )

    blood_pressure = models.CharField(
        max_length=20,
        blank=True
    )

    pulse = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    temperature = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True
    )

    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    follow_up_date = models.DateField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        if not self.prescription_id:

            last = Prescription.objects.aggregate(
                Max("prescription_id")
            )["prescription_id__max"]

            if last:
                number = int(last.replace("PRS", "")) + 1
            else:
                number = 1

            self.prescription_id = f"PRS{number:06d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.prescription_id


class PrescriptionItem(models.Model):

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name="items"
    )

    medicine = models.ForeignKey(
        Medicine,
        on_delete=models.CASCADE
    )

    dosage = models.CharField(
        max_length=100
    )

    morning = models.BooleanField(default=False)

    afternoon = models.BooleanField(default=False)

    night = models.BooleanField(default=False)

    days = models.PositiveIntegerField()

    instruction = models.CharField(
        max_length=200,
        blank=True
    )

    def __str__(self):
        return self.medicine.name