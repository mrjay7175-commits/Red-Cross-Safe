from django.urls import path
from . import views

urlpatterns = [
    path("", views.prescription_list, name="prescription_list"),
    path("add/", views.add_prescription, name="add_prescription"),
    path("<int:id>/", views.prescription_detail, name="prescription_detail"),
    path("<int:id>/edit/", views.edit_prescription, name="edit_prescription"),
    path("<int:id>/delete/", views.delete_prescription, name="delete_prescription"),
    path(
    "<int:id>/pdf/",
    views.prescription_pdf,
    name="prescription_pdf"
),
]