from django import forms
from django.forms import inlineformset_factory

from .models import Prescription, PrescriptionItem


class PrescriptionForm(forms.ModelForm):

    class Meta:

        model = Prescription

        exclude = (
            "prescription_id",
            "created_at",
        )

        widgets = {

            "patient": forms.Select(
                attrs={"class": "form-select"}
            ),

            "doctor": forms.Select(
                attrs={"class": "form-select"}
            ),

            "diagnosis": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "symptoms": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "blood_pressure": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "pulse": forms.NumberInput(
                attrs={"class": "form-control"}
            ),

            "temperature": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.1"
                }
            ),

            "weight": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.1"
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3
                }
            ),

            "follow_up_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control"
                }
            ),
        }


class PrescriptionItemForm(forms.ModelForm):

    class Meta:

        model = PrescriptionItem

        exclude = (
            "prescription",
        )

        widgets = {

            "medicine": forms.Select(
                attrs={"class": "form-select"}
            ),

            "dosage": forms.TextInput(
                attrs={"class": "form-control"}
            ),

            "days": forms.NumberInput(
                attrs={"class": "form-control"}
            ),

            "instruction": forms.TextInput(
                attrs={"class": "form-control"}
            ),
        }


PrescriptionItemFormSet = inlineformset_factory(
    Prescription,
    PrescriptionItem,
    form=PrescriptionItemForm,
    extra=1,
    can_delete=True
)