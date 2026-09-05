from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import (
    Patient,
    Doctor,
    Bill,
    Medicine,
    Appointment,
    NotificationSettings,
    MedicalRecord,
    LabTest,
    Ward,
    Bed,
    Branch,
    Ambulance,
    Vaccination,
    InsuranceClaim,
)

ROLE_CHOICES = [
    ("Admin", "Admin"),
    ("Doctor", "Doctor"),
    ("Receptionist", "Receptionist"),
    ("Pharmacist", "Pharmacist"),
    ("Lab Technician", "Lab Technician"),
]


# ---------------- Patient Form ----------------

class PatientForm(forms.ModelForm):

    class Meta:
        model = Patient
        fields = "__all__"

        widgets = {

            "name": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "age": forms.NumberInput(
                attrs={"class": "form-control"}
            ),

            "gender": forms.Select(
                attrs={"class": "form-select"}
            ),

            "disease": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "doctor": forms.Select(
                attrs={"class": "form-select"}
            ),

            "phone": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "for emailing PDF bills"}
            ),

            "branch": forms.Select(
                attrs={"class": "form-select"}
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "photo": forms.ClearableFileInput(
                attrs={"class": "form-control"}
            ),

            "status": forms.Select(
                attrs={"class": "form-select"}
            ),
        }

    def clean_age(self):
        age = self.cleaned_data.get("age")
        if age is not None and (age < 0 or age > 130):
            raise forms.ValidationError("Please enter a realistic age (0-130).")
        return age

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        digits = phone.replace(" ", "").replace("-", "").replace("+", "")
        if not digits.isdigit() or not (7 <= len(digits) <= 15):
            raise forms.ValidationError("Enter a valid phone number (7-15 digits).")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        phone = cleaned_data.get("phone")

        if name and phone:
            existing = Patient.objects.filter(name__iexact=name, phone=phone)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(
                    "A patient with this exact name and phone number already exists "
                    "- please check you're not creating a duplicate record."
                )

        return cleaned_data

# ---------------- Doctor Form ----------------

class DoctorForm(forms.ModelForm):

    class Meta:

        model = Doctor

        exclude = ["doctor_id"]

        widgets = {

            "name": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "age": forms.NumberInput(
                attrs={"class":"form-control"}
            ),

            "gender": forms.Select(
                attrs={"class":"form-select"}
            ),

            "department": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "qualification": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "experience": forms.NumberInput(
                attrs={"class":"form-control"}
            ),

            "phone": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "email": forms.EmailInput(
                attrs={"class":"form-control"}
            ),

            "address": forms.Textarea(
                attrs={
                    "class":"form-control",
                    "rows":3
                }
            ),

            "photo": forms.ClearableFileInput(
                attrs={"class":"form-control"}
            ),

            "branch": forms.Select(
                attrs={"class":"form-select"}
            ),
        }

    def clean_age(self):
        age = self.cleaned_data.get("age")
        if age is not None and (age < 18 or age > 100):
            raise forms.ValidationError("Please enter a realistic age for a doctor (18-100).")
        return age

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        digits = phone.replace(" ", "").replace("-", "").replace("+", "")
        if not digits.isdigit() or not (7 <= len(digits) <= 15):
            raise forms.ValidationError("Enter a valid phone number (7-15 digits).")
        return phone

    def clean_experience(self):
        experience = self.cleaned_data.get("experience")
        if experience is not None and experience < 0:
            raise forms.ValidationError("Experience cannot be negative.")
        return experience

# ---------------- Register Form ----------------

class RegisterForm(UserCreationForm):

    email = forms.EmailField()

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "role",
            "password1",
            "password2",
        )


# ---------------- Bill Form ----------------

class BillForm(forms.ModelForm):

    class Meta:
        model = Bill

        fields = [
            "patient",
            "doctor",
            "consultation_fee",
            "medicine_charge",
            "test_charge",
            "other_charge",
        ]

        widgets = {

            "patient": forms.Select(attrs={
                "class": "form-select"
            }),

            "doctor": forms.Select(attrs={
                "class": "form-select"
            }),

            "consultation_fee": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "medicine_charge": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "test_charge": forms.NumberInput(attrs={
                "class": "form-control"
            }),

            "other_charge": forms.NumberInput(attrs={
                "class": "form-control"
            }),

        }

    def _clean_non_negative(self, field_name):
        value = self.cleaned_data.get(field_name)
        if value is not None and value < 0:
            raise forms.ValidationError("This charge cannot be negative.")
        return value

    def clean_consultation_fee(self):
        return self._clean_non_negative("consultation_fee")

    def clean_medicine_charge(self):
        return self._clean_non_negative("medicine_charge")

    def clean_test_charge(self):
        return self._clean_non_negative("test_charge")

    def clean_other_charge(self):
        return self._clean_non_negative("other_charge")

 # ---------------- Medicine ----------------
       

class MedicineForm(forms.ModelForm):

    class Meta:

        model = Medicine

        fields = "__all__"

        widgets = {

            "expiry_date": forms.DateInput(
                attrs={
                    "type":"date",
                    "class":"form-control"
                }
            ),

            "name": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "company": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "category": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "price": forms.NumberInput(
                attrs={"class":"form-control"}
            ),

            "quantity": forms.NumberInput(
                attrs={"class":"form-control"}
            ),

            "reorder_level": forms.NumberInput(
                attrs={"class":"form-control"}
            ),

            "description": forms.Textarea(
                attrs={
                    "class":"form-control",
                    "rows":3
                }
            ),

        }

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is not None and price <= 0:
            raise forms.ValidationError("Price must be greater than zero.")
        return price

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity is not None and quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative.")
        return quantity

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get("expiry_date")
        import datetime
        if expiry_date and expiry_date < datetime.date.today():
            raise forms.ValidationError("Expiry date cannot be in the past.")
        return expiry_date

# ---------------- Appointment ----------------

class AppointmentForm(forms.ModelForm):

    class Meta:

        model = Appointment

        fields = "__all__"

        widgets = {

            "appointment_date": forms.DateInput(
                attrs={
                    "type":"date",
                    "class":"form-control"
                }
            ),

            "appointment_time": forms.TimeInput(
                attrs={
                    "type":"time",
                    "class":"form-control"
                }
            ),

            "patient": forms.Select(
                attrs={"class":"form-select"}
            ),

            "doctor": forms.Select(
                attrs={"class":"form-select"}
            ),

            "reason": forms.Textarea(
                attrs={
                    "class":"form-control",
                    "rows":3
                }
            ),

            "status": forms.Select(
                attrs={"class":"form-select"}
            ),

        }

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get("doctor")
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")

        if doctor and appointment_date and appointment_time:
            clashing = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
            ).exclude(status="Cancelled")

            if self.instance.pk:
                clashing = clashing.exclude(pk=self.instance.pk)

            if clashing.exists():
                raise forms.ValidationError(
                    f"Dr. {doctor.name} already has an appointment at "
                    f"{appointment_time} on {appointment_date}. Please pick another slot."
                )

        return cleaned_data

# ---------------- Profile Form ----------------

from django.contrib.auth.models import User

class ProfileForm(forms.ModelForm):

    class Meta:

        model = User

        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
        ]

        widgets = {

            "username": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "first_name": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "last_name": forms.TextInput(
                attrs={"class":"form-control"}
            ),

            "email": forms.EmailInput(
                attrs={"class":"form-control"}
            ),

        }


class NotificationSettingsForm(forms.ModelForm):

    class Meta:

        model = NotificationSettings

        fields = [
            "email_notification",
            "sms_notification",
            "desktop_notification",
            "phone_number",
        ]

        widgets = {
            "phone_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "+91XXXXXXXXXX"
            }),
        }


# ---------------- Lab Test ----------------

class LabTestForm(forms.ModelForm):

    class Meta:

        model = LabTest

        fields = [
            "doctor",
            "test_name",
            "normal_range",
            "result",
            "status",
            "report_file",
        ]

        widgets = {

            "doctor": forms.Select(attrs={"class": "form-select"}),

            "test_name": forms.TextInput(attrs={"class": "form-control"}),

            "normal_range": forms.TextInput(attrs={"class": "form-control"}),

            "result": forms.TextInput(attrs={"class": "form-control"}),

            "status": forms.Select(attrs={"class": "form-select"}),

            "report_file": forms.ClearableFileInput(attrs={"class": "form-control"}),

        }


# ---------------- Bed Management ----------------

class WardForm(forms.ModelForm):

    class Meta:
        model = Ward
        fields = ["name", "floor"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "floor": forms.TextInput(attrs={"class": "form-control"}),
        }


class BedForm(forms.ModelForm):

    class Meta:
        model = Bed
        fields = ["ward", "bed_number"]
        widgets = {
            "ward": forms.Select(attrs={"class": "form-select"}),
            "bed_number": forms.TextInput(attrs={"class": "form-control"}),
        }


# ---------------- Medical Record / Lab Report ----------------

class MedicalRecordForm(forms.ModelForm):

    class Meta:

        model = MedicalRecord

        fields = [
            "doctor",
            "diagnosis",
            "notes",
            "report_file",
        ]

        widgets = {

            "doctor": forms.Select(attrs={"class": "form-select"}),

            "diagnosis": forms.TextInput(attrs={"class": "form-control"}),

            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),

            "report_file": forms.ClearableFileInput(attrs={"class": "form-control"}),

        }

# ---------------- Branch ----------------

class BranchForm(forms.ModelForm):

    class Meta:
        model = Branch
        fields = "__all__"
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "is_main": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


# ---------------- Ambulance ----------------

class AmbulanceForm(forms.ModelForm):

    class Meta:
        model = Ambulance
        fields = ["vehicle_number", "driver_name", "driver_phone", "status", "branch"]
        widgets = {
            "vehicle_number": forms.TextInput(attrs={"class": "form-control"}),
            "driver_name": forms.TextInput(attrs={"class": "form-control"}),
            "driver_phone": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "branch": forms.Select(attrs={"class": "form-select"}),
        }


class AmbulanceLocationForm(forms.ModelForm):

    class Meta:
        model = Ambulance
        fields = ["status", "latitude", "longitude"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "latitude": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
            "longitude": forms.NumberInput(attrs={"class": "form-control", "step": "0.0001"}),
        }


# ---------------- Vaccination ----------------

class VaccinationForm(forms.ModelForm):

    class Meta:
        model = Vaccination
        fields = ["vaccine_name", "dose_number", "date_given", "next_due_date", "administered_by", "notes"]
        widgets = {
            "vaccine_name": forms.TextInput(attrs={"class": "form-control"}),
            "dose_number": forms.NumberInput(attrs={"class": "form-control"}),
            "date_given": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "next_due_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "administered_by": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


# ---------------- Insurance Claim ----------------

class InsuranceClaimForm(forms.ModelForm):

    class Meta:
        model = InsuranceClaim
        fields = ["bill", "insurance_provider", "policy_number", "claim_amount", "status", "notes"]
        widgets = {
            "bill": forms.Select(attrs={"class": "form-select"}),
            "insurance_provider": forms.TextInput(attrs={"class": "form-control"}),
            "policy_number": forms.TextInput(attrs={"class": "form-control"}),
            "claim_amount": forms.NumberInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
