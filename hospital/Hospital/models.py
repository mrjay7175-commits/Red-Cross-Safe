from django.db import models
from django.contrib.auth.models import User
from django.db.models import Max
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError


def validate_file_size(value):
    """Reject uploads over 5MB - a basic safeguard against abuse/DoS via huge files."""
    max_size_mb = 5
    if value.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"File too large. Max size is {max_size_mb}MB.")

class Patient(models.Model):
    patient_id = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        blank=True,
        null=True
    )

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('Admitted', 'Admitted'),
        ('Discharged', 'Discharged'),
    ]

    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    disease = models.CharField(max_length=150)

    doctor = models.ForeignKey(
        "Doctor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patients"
    )

    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True, help_text="Used for emailing PDF bills")
    address = models.TextField()
    photo = models.ImageField(
        upload_to="patients/",
        blank=True,
        null=True,
        validators=[validate_file_size]
    )
    admission_date = models.DateField(auto_now_add=True)
    branch = models.ForeignKey(
        "Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patients"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Admitted"
    )
    discharge_date = models.DateField(
    null=True,
    blank=True
)

    def save(self, *args, **kwargs):
        if not self.patient_id:
            last = Patient.objects.aggregate(
                Max("patient_id")
            )["patient_id__max"]

            if last:
                number = int(last.replace("PAT", "")) + 1
            else:
                number = 1

            self.patient_id = f"PAT{number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.patient_id} - {self.name}"


class Doctor(models.Model):
    doctor_id = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        blank=True
    )

    GENDER = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )

    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER)
    department = models.CharField(max_length=100)
    qualification = models.CharField(max_length=150)
    experience = models.PositiveIntegerField(help_text="Years")
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    photo = models.ImageField(
        upload_to="doctors/",
        blank=True,
        null=True,
        validators=[validate_file_size]
    )
    joining_date = models.DateField(auto_now_add=True)
    branch = models.ForeignKey(
        "Branch",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctors"
    )

    def save(self, *args, **kwargs):
        if not self.doctor_id:
            last = Doctor.objects.aggregate(
                Max("doctor_id")
            )["doctor_id__max"]

            if last:
                number = int(last.replace("DOC", "")) + 1
            else:
                number = 1

            self.doctor_id = f"DOC{number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.doctor_id} - {self.name}"


# ================= BILL MODEL =================

class Bill(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE
    )

    consultation_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    medicine_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    test_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    other_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    bill_date = models.DateField(
        auto_now_add=True
    )

    def save(self, *args, **kwargs):

        self.total_amount = (
            self.consultation_fee +
            self.medicine_charge +
            self.test_charge +
            self.other_charge
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bill #{self.id} - {self.patient.name}"

    PAYMENT_STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
    ]

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="Pending"
    )

    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)


class Medicine(models.Model):

    name = models.CharField(max_length=150)

    company = models.CharField(max_length=150)

    category = models.CharField(max_length=100)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    quantity = models.PositiveIntegerField()

    reorder_level = models.PositiveIntegerField(
        default=10,
        help_text="Alert will be shown when quantity falls at or below this level"
    )

    expiry_date = models.DateField()

    description = models.TextField(
        blank=True,
        null=True
    )

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level

    @property
    def is_expiring_soon(self):
        from datetime import date, timedelta
        if not self.expiry_date:
            return False
        return date.today() <= self.expiry_date <= date.today() + timedelta(days=30)

    @property
    def is_expired(self):
        from datetime import date
        return bool(self.expiry_date and self.expiry_date < date.today())

    def __str__(self):
        return self.name

class Appointment(models.Model):

    STATUS = (
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE
    )

    appointment_date = models.DateField()

    appointment_time = models.TimeField()

    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="Pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} - {self.doctor}"

# ================= MEDICAL RECORD / LAB REPORT =================

class MedicalRecord(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="records"
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    record_date = models.DateTimeField(auto_now_add=True)

    diagnosis = models.CharField(max_length=200)

    notes = models.TextField(blank=True)

    report_file = models.FileField(
        upload_to="lab_reports/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png", "doc", "docx"]),
            validate_file_size,
        ]
    )

    def __str__(self):
        return f"{self.patient.name} - {self.diagnosis} ({self.record_date:%d-%m-%Y})"

    class Meta:
        ordering = ["-record_date"]


# ================= LAB TEST =================

class LabTest(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="lab_tests"
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    test_name = models.CharField(max_length=150)

    normal_range = models.CharField(max_length=100, blank=True)

    result = models.CharField(max_length=200, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    report_file = models.FileField(
        upload_to="lab_tests/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "jpg", "jpeg", "png", "doc", "docx"]),
            validate_file_size,
        ]
    )

    test_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-test_date"]

    def __str__(self):
        return f"{self.test_name} - {self.patient.name}"


# ================= BED MANAGEMENT =================

class Ward(models.Model):

    name = models.CharField(max_length=100)

    floor = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class Bed(models.Model):

    ward = models.ForeignKey(
        Ward,
        on_delete=models.CASCADE,
        related_name="beds"
    )

    bed_number = models.CharField(max_length=20)

    patient = models.OneToOneField(
        Patient,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bed"
    )

    class Meta:
        unique_together = ("ward", "bed_number")

    @property
    def is_occupied(self):
        return self.patient_id is not None

    def __str__(self):
        return f"{self.ward.name} - Bed {self.bed_number}"


# ================= AUDIT LOG =================

class AuditLog(models.Model):

    ACTION_CHOICES = [
        ("Created", "Created"),
        ("Updated", "Updated"),
        ("Deleted", "Deleted"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    model_name = models.CharField(max_length=100)

    object_repr = models.CharField(max_length=255)

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} {self.model_name} - {self.object_repr}"


# ================= MULTI-BRANCH SUPPORT =================

class Branch(models.Model):

    name = models.CharField(max_length=150)

    address = models.TextField(blank=True)

    phone = models.CharField(max_length=20, blank=True)

    is_main = models.BooleanField(
        default=False,
        help_text="Mark as the primary/head branch"
    )

    def __str__(self):
        return self.name


# ================= AMBULANCE MANAGEMENT / TRACKING =================

class Ambulance(models.Model):

    STATUS_CHOICES = [
        ("Available", "Available"),
        ("On Duty", "On Duty"),
        ("Maintenance", "Maintenance"),
    ]

    vehicle_number = models.CharField(max_length=30, unique=True)

    driver_name = models.CharField(max_length=100)

    driver_phone = models.CharField(max_length=20)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Available"
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Manually-updated position, used to demo tracking on a map.
    # A real deployment would feed these from a GPS device/app instead.
    latitude = models.FloatField(default=28.6139)   # defaults to New Delhi
    longitude = models.FloatField(default=77.2090)

    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vehicle_number} ({self.status})"


# ================= VACCINATION RECORDS =================

class Vaccination(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="vaccinations"
    )

    vaccine_name = models.CharField(max_length=150)

    dose_number = models.PositiveIntegerField(default=1)

    date_given = models.DateField()

    next_due_date = models.DateField(null=True, blank=True)

    administered_by = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.patient.name} - {self.vaccine_name} (Dose {self.dose_number})"

    class Meta:
        ordering = ["-date_given"]


# ================= INSURANCE CLAIMS =================

class InsuranceClaim(models.Model):

    STATUS_CHOICES = [
        ("Submitted", "Submitted"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Pending", "Pending"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="insurance_claims"
    )

    bill = models.ForeignKey(
        Bill,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    insurance_provider = models.CharField(max_length=150)

    policy_number = models.CharField(max_length=100)

    claim_amount = models.DecimalField(max_digits=10, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Submitted"
    )

    notes = models.TextField(blank=True)

    submitted_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient.name} - {self.insurance_provider} ({self.status})"

    class Meta:
        ordering = ["-submitted_date"]


class NotificationSettings(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    email_notification = models.BooleanField(default=True)

    sms_notification = models.BooleanField(default=False)

    desktop_notification = models.BooleanField(default=True)

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Used for SMS notifications (include country code, e.g. +91...)"
    )

    def __str__(self):
        return self.user.username

# ================= IN-APP NOTIFICATIONS =================

class Notification(models.Model):
    """
    Broadcast-style notification shown to all staff (low stock, expiring
    medicine, pending lab tests, etc). Read state is tracked per-user via
    the read_by M2M rather than one row per user, to keep this simple.
    """

    LEVEL_CHOICES = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("danger", "Danger"),
    ]

    message = models.CharField(max_length=255)

    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default="info")

    link_name = models.CharField(
        max_length=100, blank=True,
        help_text="URL name to link to when clicked, e.g. 'medicine_list'"
    )

    # Used to avoid creating the same alert over and over - e.g.
    # "low_stock_medicine_7" so re-running the alert check doesn't spam.
    dedupe_key = models.CharField(max_length=150, unique=True)

    read_by = models.ManyToManyField(User, blank=True, related_name="read_notifications")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message

    class Meta:
        ordering = ["-created_at"]
