from django.urls import path
from . import views

urlpatterns = [

    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Authentication
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),

    # Patient URLs
    path("patients/", views.view_patient, name="view_patient"),
    path("patients/add/", views.add_patient, name="add_patient"),
    path("patients/<int:id>/", views.patient_detail, name="patient_detail"),
    path("patients/update/<int:id>/", views.update_patient, name="update_patient"),
    path("patients/delete/<int:id>/", views.delete_patient, name="delete_patient"),
    path("patients/search/", views.search_patient, name="search_patient"),
    path("patients/discharge/<int:id>/", views.discharge_patient, name="discharge_patient"),

    # Doctor URLs
    path("doctors/", views.doctor_list, name="doctor_list"),
    path("doctors/add/", views.add_doctor, name="add_doctor"),
    path("doctors/<int:id>/", views.doctor_detail, name="doctor_detail"),
    path("doctors/update/<int:id>/", views.update_doctor, name="update_doctor"),
    path("doctors/delete/<int:id>/", views.delete_doctor, name="delete_doctor"),
    path("doctors/search/", views.search_doctor, name="search_doctor"),

    # BILLING 
    path("bills/",views.bill_list,name="bill_list"),
    path("bills/add/",views.add_bill,name="add_bill"),
    path("bills/<int:id>/",views.bill_detail,name="bill_detail"),
    path("bills/update/<int:id>/",views.update_bill,name="update_bill"),
    path("bills/delete/<int:id>/",views.delete_bill,name="delete_bill"),
    # ================= MEDICINE =================

path(
    "medicines/",
    views.medicine_list,
    name="medicine_list"
),

path(
    "medicines/add/",
    views.add_medicine,
    name="add_medicine"
),

path(
    "medicines/<int:id>/",
    views.medicine_detail,
    name="medicine_detail"
),

path(
    "medicines/update/<int:id>/",
    views.update_medicine,
    name="update_medicine"
),

path(
    "medicines/delete/<int:id>/",
    views.delete_medicine,
    name="delete_medicine"
),
# ================= APPOINTMENTS =================

path(
    "appointments/",
    views.appointment_list,
    name="appointment_list"
),

path(
    "appointments/add/",
    views.add_appointment,
    name="add_appointment"
),

path(
    "appointments/<int:id>/",
    views.appointment_detail,
    name="appointment_detail"
),

path(
    "appointments/update/<int:id>/",
    views.update_appointment,
    name="update_appointment"
),

path(
    "appointments/delete/<int:id>/",
    views.delete_appointment,
    name="delete_appointment"
),

path(
    "bill/pdf/<int:id>/",
    views.download_bill_pdf,
    name="download_bill_pdf"
),

path(
    "reports/",
    views.reports,
    name="reports"
),

path("settings/", views.settings, name="settings"),

path(
    "profile/edit/",
    views.edit_profile,
    name="edit_profile"
),

path(
    "change-password/",
    views.CustomPasswordChangeView.as_view(),
    name="change_password",
),

path(
    "backup/",
    views.backup_database,
    name="backup_database"
),

path(
    "export/patients/",
    views.export_patients_excel,
    name="export_patients_excel"
),

path(
    "export/doctors/",
    views.export_doctors_excel,
    name="export_doctors_excel"
),

# ================= MEDICAL RECORDS / LAB REPORTS =================

path(
    "patients/<int:patient_id>/records/add/",
    views.add_medical_record,
    name="add_medical_record"
),

path(
    "records/<int:id>/delete/",
    views.delete_medical_record,
    name="delete_medical_record"
),

# ================= LAB TESTS =================

path("lab-tests/", views.lab_test_list, name="lab_test_list"),
path("lab-tests/add/", views.add_lab_test, name="add_lab_test"),
path("lab-tests/<int:id>/update/", views.update_lab_test, name="update_lab_test"),
path("lab-tests/<int:id>/delete/", views.delete_lab_test, name="delete_lab_test"),

# ================= BED MANAGEMENT =================

path("beds/", views.bed_list, name="bed_list"),
path("wards/add/", views.add_ward, name="add_ward"),
path("beds/add/", views.add_bed, name="add_bed"),
path("beds/<int:id>/assign/", views.assign_bed, name="assign_bed"),
path("beds/<int:id>/release/", views.release_bed, name="release_bed"),

# ================= DISCHARGE SUMMARY PDF =================

path(
    "patients/<int:id>/discharge-summary/",
    views.discharge_summary_pdf,
    name="discharge_summary_pdf"
),

# ================= PAYMENTS =================

path("bills/<int:id>/pay/", views.pay_bill, name="pay_bill"),

# ================= AUDIT LOG =================

path("audit-logs/", views.audit_log_list, name="audit_log_list"),

# ================= MULTI-BRANCH =================

path("branches/", views.branch_list, name="branch_list"),
path("branches/add/", views.add_branch, name="add_branch"),
path("branches/<int:id>/update/", views.update_branch, name="update_branch"),
path("branches/<int:id>/delete/", views.delete_branch, name="delete_branch"),

# ================= AMBULANCE =================

path("ambulances/", views.ambulance_list, name="ambulance_list"),
path("ambulances/add/", views.add_ambulance, name="add_ambulance"),
path("ambulances/<int:id>/update/", views.update_ambulance, name="update_ambulance"),
path("ambulances/<int:id>/delete/", views.delete_ambulance, name="delete_ambulance"),
path("ambulances/tracker/", views.ambulance_tracker, name="ambulance_tracker"),
path("ambulances/<int:id>/location/", views.update_ambulance_location, name="update_ambulance_location"),
path("ambulances/positions.json", views.ambulance_positions_json, name="ambulance_positions_json"),

# ================= VACCINATION =================

path("patients/<int:patient_id>/vaccinations/", views.vaccination_list, name="vaccination_list"),
path("vaccinations/<int:id>/delete/", views.delete_vaccination, name="delete_vaccination"),

# ================= INSURANCE CLAIMS =================

path("insurance-claims/", views.insurance_claim_list, name="insurance_claim_list"),
path("insurance-claims/add/", views.add_insurance_claim, name="add_insurance_claim"),
path("insurance-claims/<int:id>/update/", views.update_insurance_claim, name="update_insurance_claim"),
path("insurance-claims/<int:id>/delete/", views.delete_insurance_claim, name="delete_insurance_claim"),

# ================= QR CODE / CHECK-IN =================

path("patients/<int:id>/qr/", views.patient_qr_code, name="patient_qr_code"),
path("checkin/", views.checkin_scan, name="checkin_scan"),
path("checkin/lookup/", views.checkin_lookup, name="checkin_lookup"),

# ================= BARCODE =================

path("patients/<int:id>/barcode/", views.patient_barcode, name="patient_barcode"),
path("patients/<int:id>/barcode/label/", views.patient_barcode_label, name="patient_barcode_label"),

# ================= GLOBAL SEARCH =================

path("search/", views.global_search, name="global_search"),

# ================= DOCTOR CALENDAR =================

path("doctor-calendar/", views.doctor_calendar, name="doctor_calendar"),
path("doctor-calendar/events.json", views.doctor_calendar_events, name="doctor_calendar_events"),

# ================= DASHBOARD STATS (POLLING) =================

path("dashboard/stats.json", views.dashboard_stats_json, name="dashboard_stats_json"),

# ================= EMAIL BILL =================

path("bills/<int:id>/email/", views.email_bill_pdf, name="email_bill_pdf"),

# ================= NOTIFICATIONS =================

path("notifications.json", views.notifications_json, name="notifications_json"),
path("notifications/<int:id>/read/", views.mark_notification_read, name="mark_notification_read"),
path("notifications/read-all/", views.mark_all_notifications_read, name="mark_all_notifications_read"),

# ================= HOSPITAL ANALYTICS =================

path("analytics/", views.hospital_analytics, name="hospital_analytics"),

# ================= DEPARTMENT SUGGESTION (rule-based) =================

path("suggest-department/", views.suggest_department, name="suggest_department"),

]