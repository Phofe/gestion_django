from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("etudiants/", views.students, name="students"),
    path("enseignants/", views.teachers, name="teachers"),
    path("cours/", views.courses, name="courses"),
    path("notes/", views.grades, name="grades"),
    path("paiements/", views.payments, name="payments"),
    path("emplois-du-temps/", views.schedules, name="schedules"),
    path("notifications/", views.notifications, name="notifications"),
    path("documents/releve/", views.transcript_pdf, name="transcript_pdf"),
    path("documents/attestation/", views.certificate_pdf, name="certificate_pdf"),
    path("documents/recu/<int:payment_id>/", views.receipt_pdf, name="receipt_pdf"),
]
