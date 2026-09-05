from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import PasswordChangeView
from django.contrib.auth.models import Group
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Sum, F, Count, Q
from django.db.models.functions import TruncMonth
import json
from django.utils import timezone
from django.http import HttpResponse, FileResponse
from django.template.loader import get_template
from django.conf import settings as django_settings
from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.core.serializers.json import DjangoJSONEncoder
from django.core.cache import cache
import logging
import io
import base64

from openpyxl import Workbook
from xhtml2pdf import pisa
import qrcode
import barcode
from barcode.writer import ImageWriter

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
    AuditLog,
    Branch,
    Ambulance,
    Vaccination,
    InsuranceClaim,
    Notification,
)

from .alerts import generate_alerts

from .forms import (
    RegisterForm,
    PatientForm,
    DoctorForm,
    BillForm,
    MedicineForm,
    AppointmentForm,
    NotificationSettingsForm,
    ProfileForm,
    MedicalRecordForm,
    LabTestForm,
    WardForm,
    BedForm,
    BranchForm,
    AmbulanceForm,
    AmbulanceLocationForm,
    VaccinationForm,
    InsuranceClaimForm,
)

sms_logger = logging.getLogger("hospital.sms")


def notify_sms(user, message):
    """
    Send an SMS notification if the user has SMS notifications enabled
    and a phone number on file. No SMS gateway is wired up by default (that
    needs a paid account), so this currently just logs the message that
    would be sent - visible in the console/server logs during development.

    To send real SMS, plug in a provider here, e.g. with Twilio:

        from twilio.rest import Client
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        client.messages.create(body=message, from_=TWILIO_NUMBER, to=phone)
    """
    try:
        settings_obj, _ = NotificationSettings.objects.get_or_create(user=user)

        if settings_obj.sms_notification and settings_obj.phone_number:

            sms_logger.info(
                "[SMS to %s] %s", settings_obj.phone_number, message
            )

    except Exception:
        pass


def notify_user(user, subject, message):
    """
    Send an email notification to a staff user if they have email
    notifications enabled in their NotificationSettings. Fails silently
    so a missing/broken email backend never breaks the actual request.
    Also triggers the SMS hook (see notify_sms) if SMS is enabled.
    """
    try:
        settings_obj, _ = NotificationSettings.objects.get_or_create(user=user)

        if settings_obj.email_notification and user.email:

            send_mail(
                subject,
                message,
                django_settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )

    except Exception:
        pass

    notify_sms(user, f"{subject}: {message}")
def has_role(user, role):
    return user.groups.filter(name=role).exists()

@login_required
def dashboard(request):

    # Cheap, throttled alert scan - runs at most once every 5 minutes
    # regardless of how many people load the dashboard, so notifications
    # stay fresh without needing a real background scheduler. For
    # production, also schedule `manage.py generate_alerts` via cron for
    # alerts to appear even when nobody has the dashboard open.
    if cache.get("alerts_last_run") is None:
        try:
            generate_alerts()
        except Exception:
            pass
        cache.set("alerts_last_run", True, timeout=300)

    total_patients = Patient.objects.count()

    total_doctors = Doctor.objects.count()

    admitted = Patient.objects.filter(
        status="Admitted"
    ).count()

    discharged = Patient.objects.filter(
        status="Discharged"
    ).count()

    total_bills = Bill.objects.count()

    revenue = Bill.objects.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    recent_patients = Patient.objects.select_related("doctor").order_by("-id")[:5]

    recent_bills = Bill.objects.select_related("patient", "doctor").order_by("-id")[:5]

    # ---- Chart data ----

    six_months_ago = timezone.now() - timezone.timedelta(days=180)

    monthly_revenue_qs = (
        Bill.objects.filter(bill_date__gte=six_months_ago)
        .annotate(month=TruncMonth("bill_date"))
        .values("month")
        .annotate(total=Sum("total_amount"))
        .order_by("month")
    )

    revenue_labels = [m["month"].strftime("%b %Y") for m in monthly_revenue_qs]
    revenue_totals = [float(m["total"] or 0) for m in monthly_revenue_qs]

    appointment_status_qs = (
        Appointment.objects.values("status").annotate(count=Count("id"))
    )
    appointment_status_labels = [a["status"] for a in appointment_status_qs]
    appointment_status_counts = [a["count"] for a in appointment_status_qs]

    low_stock_count = Medicine.objects.filter(
        quantity__lte=F("reorder_level")
    ).count()

    total_beds = Bed.objects.count()
    occupied_beds = Bed.objects.exclude(patient=None).count()

    context = {

        "total_patients": total_patients,

        "total_doctors": total_doctors,

        "admitted": admitted,

        "discharged": discharged,

        "total_bills": total_bills,

        "revenue": revenue,

        "patients": recent_patients,

        "recent_bills": recent_bills,

        "low_stock_count": low_stock_count,

        "total_beds": total_beds,

        "occupied_beds": occupied_beds,

        "available_beds": total_beds - occupied_beds,

        "revenue_labels_json": json.dumps(revenue_labels),

        "revenue_totals_json": json.dumps(revenue_totals),

        "appointment_status_labels_json": json.dumps(appointment_status_labels),

        "appointment_status_counts_json": json.dumps(appointment_status_counts),

        "patient_status_labels_json": json.dumps(["Admitted", "Discharged"]),

        "patient_status_counts_json": json.dumps([admitted, discharged]),

    }

    if has_role(request.user, "Admin"):

        return render(
            request,
            "Hospital/admin_dashboard.html",
            context
        )

    elif has_role(request.user, "Doctor"):

        return render(
            request,
            "Hospital/doctor_dashboard.html",
            context
        )

    elif has_role(request.user, "Receptionist"):

        return render(
            request,
            "Hospital/reception_dashboard.html",
            context
        )

    elif has_role(request.user, "Pharmacist"):

        return render(
            request,
            "Hospital/pharmacy_dashboard.html",
            context
        )

    elif has_role(request.user, "Lab Technician"):

        return render(
            request,
            "Hospital/lab_dashboard.html",
            context
        )

    return render(
        request,
        "Hospital/dashboard.html",
        context
    )

@login_required
@permission_required("Hospital.add_patient", raise_exception=True)
def add_patient(request):

    if request.method == "POST":

        form = PatientForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            form.save()

            return redirect("view_patient")

    else:

        form = PatientForm()

    return render(
        request,
        "Hospital/add_patient.html",
        {
            "form": form
        }
    )

@login_required
@permission_required("Hospital.view_patient", raise_exception=True)
def view_patient(request):

    patient_list = Patient.objects.select_related("doctor", "branch").order_by("-id")

    paginator = Paginator(patient_list, 10)

    page = request.GET.get("page")

    patients = paginator.get_page(page)

    context = {

        "patients": patients,

        "admitted": Patient.objects.filter(
            status="Admitted"
        ).count(),

        "discharged": Patient.objects.filter(
            status="Discharged"
        ).count(),

        "total_doctors": Doctor.objects.count(),

        "total_patients": Patient.objects.count(),

    }

    return render(
        request,
        "Hospital/view_patient.html",
        context
    )

@login_required
@permission_required("Hospital.view_patient", raise_exception=True)
def patient_detail(request, id):

    patient = get_object_or_404(
        Patient,
        id=id
    )

    records = patient.records.all()

    record_form = MedicalRecordForm()

    lab_tests = patient.lab_tests.all()

    bed = Bed.objects.filter(patient=patient).first()

    return render(
        request,
        "Hospital/detail.html",
        {
            "patient": patient,

            "records": records,

            "record_form": record_form,

            "lab_tests": lab_tests,

            "bed": bed,
        }
    )


@login_required
@permission_required("Hospital.add_patient", raise_exception=True)
def add_medical_record(request, patient_id):

    patient = get_object_or_404(Patient, id=patient_id)

    if request.method == "POST":

        form = MedicalRecordForm(request.POST, request.FILES)

        if form.is_valid():

            record = form.save(commit=False)

            record.patient = patient

            record.save()

    return redirect("patient_detail", id=patient.id)


@login_required
@permission_required("Hospital.delete_patient", raise_exception=True)
def delete_medical_record(request, id):

    record = get_object_or_404(MedicalRecord, id=id)

    patient_id = record.patient.id

    record.delete()

    return redirect("patient_detail", id=patient_id)

@login_required
@permission_required("Hospital.change_patient", raise_exception=True)
def update_patient(request, id):

    patient = get_object_or_404(
        Patient,
        id=id
    )

    if request.method == "POST":

        form = PatientForm(
            request.POST,
            request.FILES,
            instance=patient
        )

        if form.is_valid():

            form.save()

            return redirect("view_patient")

    else:

        form = PatientForm(
            instance=patient
        )

    return render(
        request,
        "Hospital/update_patient.html",
        {
            "form": form
        }
    )

@login_required
@permission_required("Hospital.delete_patient", raise_exception=True)
def delete_patient(request, id):

    patient = get_object_or_404(
        Patient,
        id=id
    )

    if request.method == "POST":

        patient.delete()

        return redirect("view_patient")

    return render(
        request,
        "Hospital/delete_patient.html",
        {
            "patient": patient
        }
    )

@login_required
@permission_required("Hospital.view_patient", raise_exception=True)
def search_patient(request):

    query = request.GET.get("q", "")

    status = request.GET.get("status", "")

    gender = request.GET.get("gender", "")

    patients = Patient.objects.select_related("doctor", "branch").order_by("-id")

    if query:

        patients = patients.filter(
            name__icontains=query
        )

    if status:

        patients = patients.filter(status=status)

    if gender:

        patients = patients.filter(gender=gender)

    paginator = Paginator(patients, 10)

    page = request.GET.get("page")

    patients_page = paginator.get_page(page)

    return render(
        request,
        "Hospital/view_patient.html",
        {
            "patients": patients_page,

            "admitted": Patient.objects.filter(
                status="Admitted"
            ).count(),

            "discharged": Patient.objects.filter(
                status="Discharged"
            ).count(),

            "total_doctors": Doctor.objects.count(),

            "total_patients": Patient.objects.count(),

            "query": query,

            "status_filter": status,

            "gender_filter": gender,
        }
    )

@login_required
@permission_required("Hospital.change_patient", raise_exception=True)
def discharge_patient(request, id):
    patient = get_object_or_404(Patient, id=id)

    patient.status = "Discharged"
    patient.discharge_date = timezone.now().date()
    patient.save()

    # free up their bed, if any, on discharge
    Bed.objects.filter(patient=patient).update(patient=None)

    return redirect("view_patient")

def register(request):

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save()

            role = form.cleaned_data.get("role")

            if role:
                group, _ = Group.objects.get_or_create(name=role)
                user.groups.add(group)

            NotificationSettings.objects.get_or_create(user=user)

            login(request, user)

            return redirect("dashboard")

    else:

        form = RegisterForm()

    return render(
        request,
        "Hospital/register.html",
        {
            "form": form
        }
    )

def user_login(request):

    if request.method == "POST":

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            username = form.cleaned_data["username"]

            password = form.cleaned_data["password"]

            user = authenticate(
                username=username,
                password=password
            )

            if user:

                login(request, user)

                return redirect("dashboard")

    else:

        form = AuthenticationForm()

    return render(
        request,
        "Hospital/login.html",
        {
            "form": form
        }
    )

@login_required
def user_logout(request):

    logout(request)

    return redirect("login")

@login_required
@permission_required("Hospital.view_doctor", raise_exception=True)
def doctor_list(request):

    doctor_list = Doctor.objects.select_related("branch").order_by("-id")

    paginator = Paginator(
        doctor_list,
        10
    )

    page = request.GET.get("page")

    doctors = paginator.get_page(page)

    return render(
        request,
        "Hospital/doctor_list.html",
        {
            "doctors": doctors,

            "total_doctors": Doctor.objects.count()
        }
    )

@login_required
@permission_required("Hospital.add_doctor", raise_exception=True)
def add_doctor(request):

    if request.method == "POST":

        form = DoctorForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            form.save()

            return redirect("doctor_list")

    else:

        form = DoctorForm()

    return render(
        request,
        "Hospital/add_doctor.html",
        {
            "form": form
        }
    )

@login_required
@permission_required("Hospital.view_doctor", raise_exception=True)
def doctor_detail(request, id):

    doctor = get_object_or_404(
        Doctor,
        id=id
    )

    return render(
        request,
        "Hospital/doctor_detail.html",
        {
            "doctor": doctor
        }
    )

@login_required
@permission_required("Hospital.change_doctor", raise_exception=True)
def update_doctor(request, id):

    doctor = get_object_or_404(
        Doctor,
        id=id
    )

    if request.method == "POST":

        form = DoctorForm(
            request.POST,
            request.FILES,
            instance=doctor
        )

        if form.is_valid():

            form.save()

            return redirect("doctor_list")

    else:

        form = DoctorForm(
            instance=doctor
        )

    return render(
        request,
        "Hospital/update_doctor.html",
        {
            "form": form
        }
    )

@login_required
@permission_required("Hospital.delete_doctor", raise_exception=True)
def delete_doctor(request, id):

    doctor = get_object_or_404(
        Doctor,
        id=id
    )

    if request.method == "POST":

        doctor.delete()

        return redirect("doctor_list")

    return render(
        request,
        "Hospital/delete_doctor.html",
        {
            "doctor": doctor
        }
    )
@login_required
@permission_required("Hospital.view_doctor", raise_exception=True)
def search_doctor(request):

    query = request.GET.get("q", "")

    department = request.GET.get("department", "")

    doctors = Doctor.objects.select_related("branch").all()

    if query:

        doctors = doctors.filter(
            name__icontains=query
        )

    if department:

        doctors = doctors.filter(
            department__icontains=department
        )

    doctors = doctors.order_by("-id")

    paginator = Paginator(doctors, 10)

    page = request.GET.get("page")

    doctors_page = paginator.get_page(page)

    return render(
        request,
        "Hospital/doctor_list.html",
        {
            "doctors": doctors_page,

            "total_doctors": doctors.count(),

            "query": query,

            "department_filter": department,
        }
    )

@login_required
@permission_required("Hospital.view_bill", raise_exception=True)
def bill_list(request):

    bills = Bill.objects.select_related(
        "patient",
        "doctor"
    ).order_by("-id")

    paginator = Paginator(bills, 10)

    page = request.GET.get("page")

    bills = paginator.get_page(page)

    context = {

        "bills": bills,

        "total_bills": Bill.objects.count(),

        "total_revenue": Bill.objects.aggregate(
            total=Sum("total_amount")
        )["total"] or 0,

    }

    return render(
        request,
        "Hospital/bill_list.html",
        context
    )

@login_required
@permission_required("Hospital.add_bill", raise_exception=True)
def add_bill(request):

    if request.method == "POST":

        form = BillForm(request.POST)

        if form.is_valid():

            bill = form.save()

            notify_user(
                request.user,
                "Bill Generated",
                f"A bill of Rs. {bill.total_amount} has been generated "
                f"for {bill.patient.name}.",
            )

            return redirect("bill_list")

    else:

        form = BillForm()

    return render(
        request,
        "Hospital/add_bill.html",
        {
            "form": form
        }
    )

@login_required
@permission_required("Hospital.view_bill", raise_exception=True)
def bill_detail(request, id):

    bill = get_object_or_404(
        Bill,
        id=id
    )

    return render(
        request,
        "Hospital/bill_detail.html",
        {
            "bill": bill
        }
    )

@login_required
@permission_required("Hospital.change_bill", raise_exception=True)
def update_bill(request, id):

    bill = get_object_or_404(
        Bill,
        id=id
    )

    if request.method == "POST":

        form = BillForm(
            request.POST,
            instance=bill
        )

        if form.is_valid():

            form.save()

            return redirect("bill_list")

    else:

        form = BillForm(
            instance=bill
        )

    return render(
        request,
        "Hospital/update_bill.html",
        {
            "form": form
        }
    )

@login_required
@permission_required("Hospital.delete_bill", raise_exception=True)
def delete_bill(request, id):

    bill = get_object_or_404(
        Bill,
        id=id
    )

    if request.method == "POST":

        bill.delete()

        return redirect("bill_list")

    return render(
        request,
        "Hospital/delete_bill.html",
        {
            "bill": bill
        }
    )

@login_required
@permission_required("Hospital.view_bill", raise_exception=True)
def download_bill_pdf(request, id):

    bill = get_object_or_404(
        Bill,
        id=id
    )

    template = get_template(
        "Hospital/bill_pdf.html"
    )

    html = template.render(
        {
            "bill": bill
        }
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'filename="Bill_{bill.id}.pdf"'
    )

    pisa.CreatePDF(
        html,
        dest=response
    )

    return response

# ======================================
# MEDICINE MODULE
# ======================================

@login_required
@permission_required("Hospital.view_medicine", raise_exception=True)
def medicine_list(request):

    medicines = Medicine.objects.all().order_by("-id")

    paginator = Paginator(medicines, 10)

    page = request.GET.get("page")

    medicines = paginator.get_page(page)

    from datetime import date, timedelta
    expiring_cutoff = date.today() + timedelta(days=30)

    context = {

        "medicines": medicines,

        "total_medicines": Medicine.objects.count(),

        "low_stock_count": Medicine.objects.filter(
            quantity__lte=F("reorder_level")
        ).count(),

        "expiring_count": Medicine.objects.filter(
            expiry_date__gte=date.today(),
            expiry_date__lte=expiring_cutoff,
        ).count(),

    }

    return render(
        request,
        "Hospital/medicine_list.html",
        context
    )


@login_required
@permission_required("Hospital.add_medicine", raise_exception=True)
def add_medicine(request):

    if request.method == "POST":

        form = MedicineForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect("medicine_list")

    else:

        form = MedicineForm()

    return render(
        request,
        "Hospital/add_medicine.html",
        {
            "form": form
        }
    )


@login_required
@permission_required("Hospital.view_medicine", raise_exception=True)
def medicine_detail(request, id):

    medicine = get_object_or_404(
        Medicine,
        id=id
    )

    return render(
        request,
        "Hospital/medicine_detail.html",
        {
            "medicine": medicine
        }
    )


@login_required
@permission_required("Hospital.change_medicine", raise_exception=True)
def update_medicine(request, id):

    medicine = get_object_or_404(
        Medicine,
        id=id
    )

    if request.method == "POST":

        form = MedicineForm(
            request.POST,
            instance=medicine
        )

        if form.is_valid():

            form.save()

            return redirect("medicine_list")

    else:

        form = MedicineForm(
            instance=medicine
        )

    return render(
        request,
        "Hospital/update_medicine.html",
        {
            "form": form
        }
    )


@login_required
@permission_required("Hospital.delete_medicine", raise_exception=True)
def delete_medicine(request, id):

    medicine = get_object_or_404(
        Medicine,
        id=id
    )

    if request.method == "POST":

        medicine.delete()

        return redirect("medicine_list")

    return render(
        request,
        "Hospital/delete_medicine.html",
        {
            "medicine": medicine
        }
    )

# ======================================
# APPOINTMENT MODULE
# ======================================

@login_required
@permission_required("Hospital.view_appointment", raise_exception=True)
def appointment_list(request):

    appointments = Appointment.objects.select_related(
        "patient",
        "doctor"
    ).order_by("-id")

    paginator = Paginator(appointments, 10)

    page = request.GET.get("page")

    appointments = paginator.get_page(page)

    context = {

        "appointments": appointments,

        "total_appointments": Appointment.objects.count(),

    }

    return render(
        request,
        "Hospital/appointment_list.html",
        context
    )


@login_required
@permission_required("Hospital.add_appointment", raise_exception=True)
def add_appointment(request):

    if request.method == "POST":

        form = AppointmentForm(request.POST)

        if form.is_valid():

            appointment = form.save()

            notify_user(
                request.user,
                "Appointment Scheduled",
                f"Appointment for {appointment.patient.name} with "
                f"{appointment.doctor.name} has been scheduled on "
                f"{appointment.appointment_date} at {appointment.appointment_time}.",
            )

            return redirect("appointment_list")

    else:

        form = AppointmentForm()

    return render(
        request,
        "Hospital/add_appointment.html",
        {
            "form": form
        }
    )


@login_required
@permission_required("Hospital.view_appointment", raise_exception=True)
def appointment_detail(request, id):

    appointment = get_object_or_404(
        Appointment,
        id=id
    )

    return render(
        request,
        "Hospital/appointment_detail.html",
        {
            "appointment": appointment
        }
    )


@login_required
@permission_required("Hospital.change_appointment", raise_exception=True)
def update_appointment(request, id):

    appointment = get_object_or_404(
        Appointment,
        id=id
    )

    if request.method == "POST":

        form = AppointmentForm(
            request.POST,
            instance=appointment
        )

        if form.is_valid():

            form.save()

            return redirect("appointment_list")

    else:

        form = AppointmentForm(
            instance=appointment
        )

    return render(
        request,
        "Hospital/update_appointment.html",
        {
            "form": form
        }
    )


@login_required
@permission_required("Hospital.delete_appointment", raise_exception=True)
def delete_appointment(request, id):

    appointment = get_object_or_404(
        Appointment,
        id=id
    )

    if request.method == "POST":

        appointment.delete()

        return redirect("appointment_list")

    return render(
        request,
        "Hospital/delete_appointment.html",
        {
            "appointment": appointment
        }
    )

# ======================================
# LAB TESTS
# ======================================

@login_required
@permission_required("Hospital.view_labtest", raise_exception=True)
def lab_test_list(request):

    tests = LabTest.objects.select_related("patient", "doctor").order_by("-test_date")

    paginator = Paginator(tests, 10)

    page = request.GET.get("page")

    return render(
        request,
        "Hospital/lab_test_list.html",
        {
            "tests": paginator.get_page(page),
            "pending_count": LabTest.objects.filter(status="Pending").count(),
        }
    )


@login_required
@permission_required("Hospital.add_labtest", raise_exception=True)
def add_lab_test(request):

    if request.method == "POST":

        form = LabTestForm(request.POST, request.FILES)

        if form.is_valid():

            test = form.save(commit=False)

            patient_id = request.POST.get("patient")

            test.patient = get_object_or_404(Patient, id=patient_id)

            test.save()

            return redirect("lab_test_list")

    else:

        form = LabTestForm()

    return render(
        request,
        "Hospital/add_lab_test.html",
        {
            "form": form,
            "patients": Patient.objects.all().order_by("name"),
        }
    )


@login_required
@permission_required("Hospital.change_labtest", raise_exception=True)
def update_lab_test(request, id):

    test = get_object_or_404(LabTest, id=id)

    if request.method == "POST":

        form = LabTestForm(request.POST, request.FILES, instance=test)

        if form.is_valid():

            form.save()

            return redirect("lab_test_list")

    else:

        form = LabTestForm(instance=test)

    return render(
        request,
        "Hospital/update_lab_test.html",
        {
            "form": form,
            "test": test,
        }
    )


@login_required
@permission_required("Hospital.delete_labtest", raise_exception=True)
def delete_lab_test(request, id):

    test = get_object_or_404(LabTest, id=id)

    if request.method == "POST":

        test.delete()

        return redirect("lab_test_list")

    return render(
        request,
        "Hospital/delete_lab_test.html",
        {
            "test": test
        }
    )


# ======================================
# BED MANAGEMENT
# ======================================

@login_required
@permission_required("Hospital.view_bed", raise_exception=True)
def bed_list(request):

    wards = Ward.objects.prefetch_related("beds", "beds__patient").order_by("name")

    return render(
        request,
        "Hospital/bed_list.html",
        {
            "wards": wards,
            "total_beds": Bed.objects.count(),
            "occupied_beds": Bed.objects.exclude(patient=None).count(),
            "available_beds": Bed.objects.filter(patient=None).count(),
            "available_patients": Patient.objects.filter(status="Admitted", bed=None),
        }
    )


@login_required
@permission_required("Hospital.add_ward", raise_exception=True)
def add_ward(request):

    if request.method == "POST":

        form = WardForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect("bed_list")

    else:

        form = WardForm()

    return render(
        request,
        "Hospital/add_ward.html",
        {
            "form": form
        }
    )


@login_required
@permission_required("Hospital.add_bed", raise_exception=True)
def add_bed(request):

    if request.method == "POST":

        form = BedForm(request.POST)

        if form.is_valid():

            form.save()

            return redirect("bed_list")

    else:

        form = BedForm()

    return render(
        request,
        "Hospital/add_bed.html",
        {
            "form": form
        }
    )


@login_required
@permission_required("Hospital.change_bed", raise_exception=True)
def assign_bed(request, id):

    bed = get_object_or_404(Bed, id=id)

    if request.method == "POST":

        patient_id = request.POST.get("patient")

        if patient_id:

            bed.patient = get_object_or_404(Patient, id=patient_id)

            bed.save()

    return redirect("bed_list")


@login_required
@permission_required("Hospital.change_bed", raise_exception=True)
def release_bed(request, id):

    bed = get_object_or_404(Bed, id=id)

    bed.patient = None

    bed.save()

    return redirect("bed_list")


# ======================================
# DISCHARGE SUMMARY PDF
# ======================================

@login_required
@permission_required("Hospital.view_patient", raise_exception=True)
def discharge_summary_pdf(request, id):

    patient = get_object_or_404(Patient, id=id)

    bills = Bill.objects.filter(patient=patient)

    records = patient.records.all()

    total_billed = bills.aggregate(total=Sum("total_amount"))["total"] or 0

    template = get_template("Hospital/discharge_summary.html")

    html = template.render({
        "patient": patient,
        "bills": bills,
        "records": records,
        "total_billed": total_billed,
        "generated_on": timezone.now(),
    })

    response = HttpResponse(content_type="application/pdf")

    response["Content-Disposition"] = f'attachment; filename="discharge_summary_{patient.patient_id}.pdf"'

    pisa.CreatePDF(html, dest=response)

    return response


# ======================================
# BILLING - PAYMENT (SIMULATED GATEWAY)
# ======================================
# NOTE: This is a demo/simulated payment flow so the app works out of the
# box with no external accounts. To go live with real online payments,
# integrate a gateway SDK (Razorpay/Stripe/PayU) here: create an order with
# the gateway's API using their secret key, render their checkout, and mark
# the bill paid only after verifying the gateway's payment signature /
# webhook - never mark a bill paid purely on the client's say-so in
# production.

@login_required
@permission_required("Hospital.view_bill", raise_exception=True)
def pay_bill(request, id):

    bill = get_object_or_404(Bill, id=id)

    if request.method == "POST":

        bill.payment_status = "Paid"

        bill.razorpay_payment_id = f"SIMULATED-{bill.id}-{int(timezone.now().timestamp())}"

        bill.save()

        notify_user(
            request.user,
            "Payment Received",
            f"Payment of Rs. {bill.total_amount} received for {bill.patient.name} (Bill #{bill.id}).",
        )

        return redirect("bill_detail", id=bill.id)

    return render(
        request,
        "Hospital/pay_bill.html",
        {
            "bill": bill
        }
    )


# ======================================
# AUDIT LOG
# ======================================

@login_required
@permission_required("Hospital.view_auditlog", raise_exception=True)
def audit_log_list(request):

    logs = AuditLog.objects.select_related("user").all()

    action = request.GET.get("action", "")

    model_name = request.GET.get("model", "")

    if action:
        logs = logs.filter(action=action)

    if model_name:
        logs = logs.filter(model_name=model_name)

    paginator = Paginator(logs, 25)

    page = request.GET.get("page")

    return render(
        request,
        "Hospital/audit_log_list.html",
        {
            "logs": paginator.get_page(page),
            "action_filter": action,
            "model_filter": model_name,
            "model_names": AuditLog.objects.values_list("model_name", flat=True).distinct(),
        }
    )


# ======================================
# MULTI-BRANCH SUPPORT
# ======================================

@login_required
@permission_required("Hospital.view_branch", raise_exception=True)
def branch_list(request):

    branches = Branch.objects.annotate(
        patient_count=Count("patients", distinct=True),
        doctor_count=Count("doctors", distinct=True),
    ).order_by("-is_main", "name")

    return render(request, "Hospital/branch_list.html", {"branches": branches})


@login_required
@permission_required("Hospital.add_branch", raise_exception=True)
def add_branch(request):

    if request.method == "POST":
        form = BranchForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("branch_list")
    else:
        form = BranchForm()

    return render(request, "Hospital/add_branch.html", {"form": form})


@login_required
@permission_required("Hospital.change_branch", raise_exception=True)
def update_branch(request, id):

    branch = get_object_or_404(Branch, id=id)

    if request.method == "POST":
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()
            return redirect("branch_list")
    else:
        form = BranchForm(instance=branch)

    return render(request, "Hospital/update_branch.html", {"form": form, "branch": branch})


@login_required
@permission_required("Hospital.delete_branch", raise_exception=True)
def delete_branch(request, id):

    branch = get_object_or_404(Branch, id=id)

    if request.method == "POST":
        branch.delete()
        return redirect("branch_list")

    return render(request, "Hospital/delete_branch.html", {"branch": branch})


# ======================================
# AMBULANCE MANAGEMENT / LIVE TRACKING
# ======================================
# NOTE: "Live tracking" here means the map re-reads whatever lat/long is
# stored on the Ambulance record every few seconds. There's no real GPS
# hardware wired in - a real deployment would have the ambulance's
# phone/GPS unit call update_ambulance_location() periodically (e.g. from
# a driver mobile app) instead of a staff member typing coordinates in.

@login_required
@permission_required("Hospital.view_ambulance", raise_exception=True)
def ambulance_list(request):

    ambulances = Ambulance.objects.select_related("branch").order_by("vehicle_number")

    return render(
        request,
        "Hospital/ambulance_list.html",
        {
            "ambulances": ambulances,
            "available_count": ambulances.filter(status="Available").count(),
            "on_duty_count": ambulances.filter(status="On Duty").count(),
        }
    )


@login_required
@permission_required("Hospital.add_ambulance", raise_exception=True)
def add_ambulance(request):

    if request.method == "POST":
        form = AmbulanceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("ambulance_list")
    else:
        form = AmbulanceForm()

    return render(request, "Hospital/add_ambulance.html", {"form": form})


@login_required
@permission_required("Hospital.change_ambulance", raise_exception=True)
def update_ambulance(request, id):

    ambulance = get_object_or_404(Ambulance, id=id)

    if request.method == "POST":
        form = AmbulanceForm(request.POST, instance=ambulance)
        if form.is_valid():
            form.save()
            return redirect("ambulance_list")
    else:
        form = AmbulanceForm(instance=ambulance)

    return render(request, "Hospital/update_ambulance.html", {"form": form, "ambulance": ambulance})


@login_required
@permission_required("Hospital.delete_ambulance", raise_exception=True)
def delete_ambulance(request, id):

    ambulance = get_object_or_404(Ambulance, id=id)

    if request.method == "POST":
        ambulance.delete()
        return redirect("ambulance_list")

    return render(request, "Hospital/delete_ambulance.html", {"ambulance": ambulance})


@login_required
@permission_required("Hospital.view_ambulance", raise_exception=True)
def ambulance_tracker(request):
    """Map page showing every ambulance's last known position."""

    ambulances = Ambulance.objects.all()

    markers = [
        {
            "id": a.id,
            "vehicle_number": a.vehicle_number,
            "driver_name": a.driver_name,
            "status": a.status,
            "lat": a.latitude,
            "lng": a.longitude,
        }
        for a in ambulances
    ]

    return render(
        request,
        "Hospital/ambulance_tracker.html",
        {
            "ambulances": ambulances,
            "markers_json": json.dumps(markers),
        }
    )


@login_required
@permission_required("Hospital.change_ambulance", raise_exception=True)
def update_ambulance_location(request, id):
    """Manual stand-in for a real GPS device pushing its location."""

    ambulance = get_object_or_404(Ambulance, id=id)

    if request.method == "POST":
        form = AmbulanceLocationForm(request.POST, instance=ambulance)
        if form.is_valid():
            form.save()

    return redirect("ambulance_tracker")


@login_required
@permission_required("Hospital.view_ambulance", raise_exception=True)
def ambulance_positions_json(request):
    """Polled by the tracker page so positions refresh without a full reload."""

    data = [
        {
            "id": a.id,
            "vehicle_number": a.vehicle_number,
            "status": a.status,
            "lat": a.latitude,
            "lng": a.longitude,
        }
        for a in Ambulance.objects.all()
    ]

    return HttpResponse(json.dumps(data), content_type="application/json")


# ======================================
# VACCINATION RECORDS
# ======================================

@login_required
@permission_required("Hospital.view_vaccination", raise_exception=True)
def vaccination_list(request, patient_id):

    patient = get_object_or_404(Patient, id=patient_id)

    vaccinations = patient.vaccinations.all()

    if request.method == "POST":
        form = VaccinationForm(request.POST)
        if form.is_valid():
            v = form.save(commit=False)
            v.patient = patient
            v.save()
            return redirect("vaccination_list", patient_id=patient.id)
    else:
        form = VaccinationForm()

    return render(
        request,
        "Hospital/vaccination_list.html",
        {"patient": patient, "vaccinations": vaccinations, "form": form}
    )


@login_required
@permission_required("Hospital.delete_vaccination", raise_exception=True)
def delete_vaccination(request, id):

    v = get_object_or_404(Vaccination, id=id)
    patient_id = v.patient.id
    v.delete()

    return redirect("vaccination_list", patient_id=patient_id)


# ======================================
# INSURANCE CLAIMS
# ======================================

@login_required
@permission_required("Hospital.view_insuranceclaim", raise_exception=True)
def insurance_claim_list(request):

    claims = InsuranceClaim.objects.select_related("patient", "bill").order_by("-submitted_date")

    paginator = Paginator(claims, 15)

    page = request.GET.get("page")

    return render(
        request,
        "Hospital/insurance_claim_list.html",
        {"claims": paginator.get_page(page)}
    )


@login_required
@permission_required("Hospital.add_insuranceclaim", raise_exception=True)
def add_insurance_claim(request):

    if request.method == "POST":
        form = InsuranceClaimForm(request.POST)
        patient_id = request.POST.get("patient")
        if form.is_valid() and patient_id:
            claim = form.save(commit=False)
            claim.patient = get_object_or_404(Patient, id=patient_id)
            claim.save()
            return redirect("insurance_claim_list")
    else:
        form = InsuranceClaimForm()

    return render(
        request,
        "Hospital/add_insurance_claim.html",
        {"form": form, "patients": Patient.objects.all().order_by("name")}
    )


@login_required
@permission_required("Hospital.change_insuranceclaim", raise_exception=True)
def update_insurance_claim(request, id):

    claim = get_object_or_404(InsuranceClaim, id=id)

    if request.method == "POST":
        form = InsuranceClaimForm(request.POST, instance=claim)
        if form.is_valid():
            form.save()
            return redirect("insurance_claim_list")
    else:
        form = InsuranceClaimForm(instance=claim)

    return render(request, "Hospital/update_insurance_claim.html", {"form": form, "claim": claim})


@login_required
@permission_required("Hospital.delete_insuranceclaim", raise_exception=True)
def delete_insurance_claim(request, id):

    claim = get_object_or_404(InsuranceClaim, id=id)

    if request.method == "POST":
        claim.delete()
        return redirect("insurance_claim_list")

    return render(request, "Hospital/delete_insurance_claim.html", {"claim": claim})


# ======================================
# QR CODE CHECK-IN
# ======================================

@login_required
def patient_qr_code(request, id):
    """Returns a PNG QR code encoding this patient's check-in URL."""

    patient = get_object_or_404(Patient, id=id)

    checkin_url = request.build_absolute_uri(
        f"/checkin/lookup/?patient_id={patient.patient_id}"
    )

    img = qrcode.make(checkin_url)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    return HttpResponse(buffer.getvalue(), content_type="image/png")


@login_required
def checkin_scan(request):
    """Page with a camera-based QR scanner (or manual entry) for front-desk check-in."""

    return render(request, "Hospital/checkin_scan.html")


@login_required
def checkin_lookup(request):
    """Looks up a patient by the code scanned/typed and shows their record."""

    patient_id = request.GET.get("patient_id", "").strip()

    patient = Patient.objects.filter(patient_id__iexact=patient_id).first()

    if patient:
        return redirect("patient_detail", id=patient.id)

    return render(
        request,
        "Hospital/checkin_scan.html",
        {"not_found": patient_id}
    )


# ======================================
# BARCODE PRINTING
# ======================================

@login_required
def patient_barcode(request, id):
    """Returns a printable PNG barcode encoding this patient's ID."""

    patient = get_object_or_404(Patient, id=id)

    code128 = barcode.get_barcode_class("code128")

    barcode_obj = code128(patient.patient_id, writer=ImageWriter())

    buffer = io.BytesIO()

    barcode_obj.write(buffer, options={"write_text": True})

    return HttpResponse(buffer.getvalue(), content_type="image/png")


@login_required
def patient_barcode_label(request, id):
    """Printable label page (browser Print -> sticker printer)."""

    patient = get_object_or_404(Patient, id=id)

    return render(request, "Hospital/patient_barcode_label.html", {"patient": patient})


# ======================================
# GLOBAL SEARCH
# ======================================

@login_required
def global_search(request):

    query = request.GET.get("q", "").strip()

    patients = doctors = bills = medicines = []

    if query:
        patients = Patient.objects.filter(
            Q(name__icontains=query) |
            Q(patient_id__icontains=query) |
            Q(phone__icontains=query)
        )[:20]

        doctors = Doctor.objects.filter(
            Q(name__icontains=query) |
            Q(doctor_id__icontains=query) |
            Q(department__icontains=query)
        )[:20]

        bills = Bill.objects.select_related("patient").filter(
            Q(patient__name__icontains=query) |
            Q(id__icontains=query)
        )[:20]

        medicines = Medicine.objects.filter(
            Q(name__icontains=query) |
            Q(company__icontains=query)
        )[:20]

    return render(
        request,
        "Hospital/global_search.html",
        {
            "query": query,
            "patients": patients,
            "doctors": doctors,
            "bills": bills,
            "medicines": medicines,
        }
    )


# ======================================
# DOCTOR CALENDAR
# ======================================

@login_required
@permission_required("Hospital.view_appointment", raise_exception=True)
def doctor_calendar(request):

    doctors = Doctor.objects.all().order_by("name")

    selected_doctor_id = request.GET.get("doctor", "")

    return render(
        request,
        "Hospital/doctor_calendar.html",
        {
            "doctors": doctors,
            "selected_doctor_id": selected_doctor_id,
        }
    )


@login_required
@permission_required("Hospital.view_appointment", raise_exception=True)
def doctor_calendar_events(request):
    """JSON feed of appointments for FullCalendar, optionally filtered by doctor."""

    doctor_id = request.GET.get("doctor", "")

    appointments = Appointment.objects.select_related("patient", "doctor").all()

    if doctor_id:
        appointments = appointments.filter(doctor_id=doctor_id)

    events = [
        {
            "id": a.id,
            "title": f"{a.patient.name} - {a.reason or 'Appointment'}",
            "start": f"{a.appointment_date}T{a.appointment_time}",
            "color": "#dc3545" if a.status == "Cancelled" else (
                "#198754" if a.status == "Completed" else "#0d6efd"
            ),
        }
        for a in appointments
    ]

    return HttpResponse(json.dumps(events), content_type="application/json")


# ======================================
# REAL-TIME(ISH) DASHBOARD STATS
# ======================================
# True real-time would use WebSockets (Django Channels + Redis). That's a
# much heavier dependency to add to a project like this, so instead the
# dashboard polls this lightweight JSON endpoint every few seconds and
# updates the numbers in place - good enough for a live-feeling dashboard
# without needing extra infrastructure.

@login_required
def dashboard_stats_json(request):

    data = cache.get("dashboard_stats")

    if data is None:

        data = {
            "total_patients": Patient.objects.count(),
            "admitted": Patient.objects.filter(status="Admitted").count(),
            "discharged": Patient.objects.filter(status="Discharged").count(),
            "total_doctors": Doctor.objects.count(),
            "total_bills": Bill.objects.count(),
            "revenue": float(Bill.objects.aggregate(total=Sum("total_amount"))["total"] or 0),
            "low_stock_count": Medicine.objects.filter(quantity__lte=F("reorder_level")).count(),
            "occupied_beds": Bed.objects.exclude(patient=None).count(),
            "total_beds": Bed.objects.count(),
            "pending_lab_tests": LabTest.objects.filter(status="Pending").count(),
        }

        # Short cache since the dashboard polls this every few seconds -
        # avoids re-running ~10 aggregate queries per request under load.
        cache.set("dashboard_stats", data, timeout=10)

    return HttpResponse(json.dumps(data), content_type="application/json")


# ======================================
# IN-APP NOTIFICATIONS (bell icon)
# ======================================

@login_required
def notifications_json(request):
    """Polled by the navbar bell every 20s for unread notifications."""

    unread = Notification.objects.exclude(read_by=request.user).order_by("-created_at")[:15]

    data = {
        "unread_count": Notification.objects.exclude(read_by=request.user).count(),
        "notifications": [
            {
                "id": n.id,
                "message": n.message,
                "level": n.level,
                "link_name": n.link_name,
                "created_at": n.created_at.strftime("%d %b, %H:%M"),
            }
            for n in unread
        ],
    }

    return HttpResponse(json.dumps(data), content_type="application/json")


@login_required
def mark_notification_read(request, id):
    notification = get_object_or_404(Notification, id=id)
    notification.read_by.add(request.user)
    return redirect(request.POST.get("next") or "dashboard")


@login_required
def mark_all_notifications_read(request):
    for n in Notification.objects.exclude(read_by=request.user):
        n.read_by.add(request.user)
    return redirect(request.POST.get("next") or "dashboard")


# ======================================
# HOSPITAL ANALYTICS
# ======================================

@login_required
@permission_required("Hospital.view_bill", raise_exception=True)
def hospital_analytics(request):
    """Deeper analytics beyond the main dashboard - demographics, trends, top diseases."""

    gender_qs = Patient.objects.values("gender").annotate(count=Count("id"))
    gender_labels = [g["gender"] for g in gender_qs]
    gender_counts = [g["count"] for g in gender_qs]

    dept_qs = Doctor.objects.values("department").annotate(count=Count("id")).order_by("-count")
    dept_labels = [d["department"] for d in dept_qs]
    dept_counts = [d["count"] for d in dept_qs]

    twelve_months_ago = timezone.now() - timezone.timedelta(days=365)
    admissions_qs = (
        Patient.objects.filter(admission_date__gte=twelve_months_ago)
        .annotate(month=TruncMonth("admission_date"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    admission_labels = [a["month"].strftime("%b %Y") for a in admissions_qs]
    admission_counts = [a["count"] for a in admissions_qs]

    top_diseases_qs = (
        Patient.objects.exclude(disease="")
        .values("disease")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    disease_labels = [d["disease"] for d in top_diseases_qs]
    disease_counts = [d["count"] for d in top_diseases_qs]

    avg_bill_amount = (
        Bill.objects.aggregate(total=Sum("total_amount"))["total"] or 0
    ) / (Bill.objects.count() or 1)

    completed_appts = Appointment.objects.filter(status="Completed").count()
    total_appts = Appointment.objects.count()
    completion_rate = round((completed_appts / total_appts) * 100, 1) if total_appts else 0

    return render(
        request,
        "Hospital/hospital_analytics.html",
        {
            "gender_labels_json": json.dumps(gender_labels),
            "gender_counts_json": json.dumps(gender_counts),
            "dept_labels_json": json.dumps(dept_labels),
            "dept_counts_json": json.dumps(dept_counts),
            "admission_labels_json": json.dumps(admission_labels),
            "admission_counts_json": json.dumps(admission_counts),
            "disease_labels_json": json.dumps(disease_labels),
            "disease_counts_json": json.dumps(disease_counts),
            "avg_bill_amount": round(avg_bill_amount, 2),
            "completion_rate": completion_rate,
            "total_appointments": total_appts,
        }
    )


# ======================================
# RULE-BASED DEPARTMENT SUGGESTION
# ======================================
# NOTE: This is a simple keyword-matching heuristic, NOT a machine-learning
# or LLM-based system - it's intentionally lightweight so the project runs
# with zero external AI dependencies or API keys. If you want a genuinely
# smarter suggestion, swap the body of this function for a call to an LLM
# API (OpenAI/Anthropic/etc) using the symptom text as the prompt - just
# keep the same JSON response shape so the frontend doesn't need to change.

DEPARTMENT_KEYWORDS = {
    "Cardiology": ["heart", "chest pain", "cardiac", "palpitation", "blood pressure", "hypertension"],
    "Orthopedics": ["bone", "fracture", "joint", "back pain", "knee", "spine", "arthritis"],
    "Dermatology": ["skin", "rash", "acne", "eczema", "itching"],
    "Pediatrics": ["child", "infant", "baby", "kid"],
    "Ophthalmology": ["eye", "vision", "blurry"],
    "ENT": ["ear", "nose", "throat", "sinus", "hearing"],
    "Neurology": ["headache", "migraine", "seizure", "numbness", "nerve"],
    "Gastroenterology": ["stomach", "abdominal", "digestion", "liver", "acid reflux"],
    "Dentistry": ["tooth", "teeth", "gum", "dental"],
    "Gynecology": ["pregnancy", "menstrual", "gynec"],
    "Psychiatry": ["anxiety", "depression", "stress", "sleep", "insomnia"],
}


@login_required
def suggest_department(request):
    """AJAX endpoint: suggest a department from free-text symptoms via keyword matching."""

    text = request.GET.get("q", "").lower()

    matched_department = None
    for department, keywords in DEPARTMENT_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            matched_department = department
            break

    return HttpResponse(
        json.dumps({
            "suggested_department": matched_department or "General Medicine",
            "method": "rule-based keyword matching (not AI/ML)",
        }),
        content_type="application/json",
    )


# ======================================
# EMAIL PDF BILL
# ======================================

@login_required
@permission_required("Hospital.view_bill", raise_exception=True)
def email_bill_pdf(request, id):

    bill = get_object_or_404(Bill, id=id)

    if not bill.patient.email:
        return render(
            request,
            "Hospital/bill_detail.html",
            {"bill": bill, "email_error": "This patient has no email address on file."}
        )

    template = get_template("Hospital/bill_pdf.html")
    html = template.render({"bill": bill})

    pdf_buffer = io.BytesIO()
    pisa.CreatePDF(html, dest=pdf_buffer)

    email = EmailMessage(
        subject=f"Your Hospital Bill #{bill.id}",
        body=f"Dear {bill.patient.name},\n\nPlease find your bill (₹ {bill.total_amount}) attached.\n\nThank you.",
        from_email=django_settings.DEFAULT_FROM_EMAIL,
        to=[bill.patient.email],
    )
    email.attach(f"bill_{bill.id}.pdf", pdf_buffer.getvalue(), "application/pdf")
    email.send(fail_silently=True)

    return redirect("bill_detail", id=bill.id)


# ======================================
# PASSWORD CHANGE
# ======================================

class CustomPasswordChangeView(PasswordChangeView):

    template_name = "Hospital/change_password.html"

    success_url = reverse_lazy("settings")


# ======================================
# REPORTS
# ======================================

@login_required
@permission_required("Hospital.view_bill", raise_exception=True)
def reports(request):

    context = {

        "total_patients": Patient.objects.count(),

        "total_doctors": Doctor.objects.count(),

        "total_medicines": Medicine.objects.count(),

        "total_appointments": Appointment.objects.count(),

        "total_bills": Bill.objects.count(),

        "total_revenue": Bill.objects.aggregate(
            total=Sum("total_amount")
        )["total"] or 0,

    }

    return render(
        request,
        "Hospital/reports.html",
        context
    )


# ======================================
# SETTINGS
# ======================================

@login_required
def settings(request):

    notification, created = NotificationSettings.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        form = NotificationSettingsForm(
            request.POST,
            instance=notification
        )

        if form.is_valid():

            form.save()

            return redirect("settings")

    else:

        form = NotificationSettingsForm(
            instance=notification
        )

    context = {

        "form": form,

        "total_patients": Patient.objects.count(),

        "total_doctors": Doctor.objects.count(),

        "total_bills": Bill.objects.count(),

        "total_revenue": Bill.objects.aggregate(
            total=Sum("total_amount")
        )["total"] or 0,

    }

    return render(
        request,
        "Hospital/settings.html",
        context
    )


# ======================================
# EDIT PROFILE
# ======================================

@login_required
def edit_profile(request):

    if request.method == "POST":

        form = ProfileForm(
            request.POST,
            instance=request.user
        )

        if form.is_valid():

            form.save()

            return redirect("settings")

    else:

        form = ProfileForm(
            instance=request.user
        )

    return render(
        request,
        "Hospital/edit_profile.html",
        {
            "form": form
        }
    )


# ======================================
# DATABASE BACKUP
# ======================================

@login_required
@permission_required("Hospital.view_patient", raise_exception=True)
def backup_database(request):

    db_path = django_settings.DATABASES["default"]["NAME"]

    return FileResponse(
        open(db_path, "rb"),
        as_attachment=True,
        filename="hospital_backup.sqlite3"
    )


# ======================================
# EXPORT PATIENTS EXCEL
# ======================================

@login_required
@permission_required("Hospital.view_patient", raise_exception=True)
def export_patients_excel(request):

    wb = Workbook()

    ws = wb.active

    ws.title = "Patients"

    ws.append([
        "ID",
        "Name",
        "Age",
        "Gender",
        "Disease",
        "Doctor",
        "Phone",
        "Status"
    ])

    for p in Patient.objects.all():

        ws.append([
            p.id,
            p.name,
            p.age,
            p.gender,
            p.disease,
            p.doctor.name if p.doctor else "N/A",
            p.phone,
            p.status,
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = (
        'attachment; filename="Patients.xlsx"'
    )

    wb.save(response)

    return response


# ======================================
# EXPORT DOCTORS EXCEL
# ======================================

@login_required
@permission_required("Hospital.view_doctor", raise_exception=True)
def export_doctors_excel(request):

    wb = Workbook()

    ws = wb.active

    ws.title = "Doctors"

    ws.append([
    "Doctor ID",
    "Name",
    "Department",
    "Qualification",
    "Experience",
    "Phone",
    "Email",
])

    for d in Doctor.objects.all():

        ws.append([
            d.doctor_id,
            d.name,
            d.department,
            d.qualification,
            d.experience,
            d.phone,
            d.email,
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = (
        'attachment; filename="Doctors.xlsx"'
    )

    wb.save(response)

    return response


