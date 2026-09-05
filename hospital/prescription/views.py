from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from .models import Prescription
from .forms import (
    PrescriptionForm,
    PrescriptionItemFormSet,
)


def prescription_list(request):
    query = request.GET.get("q", "")

    prescriptions = Prescription.objects.select_related(
        "patient",
        "doctor"
    )

    if query:
        prescriptions = prescriptions.filter(
            Q(prescription_id__icontains=query) |
            Q(patient__name__icontains=query) |
            Q(doctor__name__icontains=query)
        )

    prescriptions = prescriptions.order_by("-id")

    return render(
        request,
        "prescription/prescription_list.html",
        {
            "prescriptions": prescriptions,
            "query": query,
        },
    )


def add_prescription(request):

    if request.method == "POST":

        form = PrescriptionForm(request.POST)

        if form.is_valid():

            prescription = form.save()

            formset = PrescriptionItemFormSet(
                request.POST,
                instance=prescription
            )

            if formset.is_valid():
                formset.save()
                return redirect("prescription_list")

        else:
            formset = PrescriptionItemFormSet(
                request.POST
            )

    else:

        form = PrescriptionForm()

        formset = PrescriptionItemFormSet()

    return render(
        request,
        "prescription/add_prescription.html",
        {
            "form": form,
            "formset": formset,
        },
    )


def prescription_detail(request, id):

    prescription = get_object_or_404(
        Prescription,
        id=id
    )

    return render(
        request,
        "prescription/prescription_detail.html",
        {
            "prescription": prescription,
        },
    )


def edit_prescription(request, id):

    prescription = get_object_or_404(
        Prescription,
        id=id
    )

    if request.method == "POST":

        form = PrescriptionForm(
            request.POST,
            instance=prescription
        )

        formset = PrescriptionItemFormSet(
            request.POST,
            instance=prescription
        )

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect(
                "prescription_detail",
                id=prescription.id
            )

    else:

        form = PrescriptionForm(
            instance=prescription
        )

        formset = PrescriptionItemFormSet(
            instance=prescription
        )

    return render(
        request,
        "prescription/add_prescription.html",
        {
            "form": form,
            "formset": formset,
        },
    )


def delete_prescription(request, id):

    prescription = get_object_or_404(
        Prescription,
        id=id
    )

    if request.method == "POST":
        prescription.delete()
        return redirect("prescription_list")

    return render(
        request,
        "prescription/delete_prescription.html",
        {
            "prescription": prescription,
        },
    )

def prescription_pdf(request, id):

    prescription = get_object_or_404(
        Prescription,
        id=id
    )

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = (
        f'attachment; filename="{prescription.prescription_id}.pdf"'
    )

    doc = SimpleDocTemplate(response)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph("<b>Hospital Prescription</b>", styles["Title"])
    )

    elements.append(
        Paragraph(
            f"Prescription ID : {prescription.prescription_id}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Patient : {prescription.patient.name}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Doctor : {prescription.doctor.name}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Diagnosis : {prescription.diagnosis}",
            styles["Normal"]
        )
    )

    data = [
        [
            "Medicine",
            "Dosage",
            "Morning",
            "Afternoon",
            "Night",
            "Days"
        ]
    ]

    for item in prescription.items.all():

        data.append(
            [
                item.medicine.name,
                item.dosage,
                "Yes" if item.morning else "No",
                "Yes" if item.afternoon else "No",
                "Yes" if item.night else "No",
                item.days,
            ]
        )

    table = Table(data)

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.darkblue),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("GRID", (0,0), (-1,-1), 1, colors.black),
            ("BACKGROUND", (0,1), (-1,-1), colors.beige),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ])
    )

    elements.append(table)

    doc.build(elements)

    return response