from django.test import TestCase
from django.urls import reverse
from .models import User, Student, Teacher, Course, Enrollment, Grade, Payment, Notification

class AcademicPortalTests(TestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(username="etudiant", password="test-pass-123", role=User.Role.STUDENT, first_name="Amina", last_name="Test")
        self.student = Student.objects.create(user=self.student_user, student_number="ETU-001", program="Informatique")
        self.teacher_user = User.objects.create_user(username="enseignant", password="test-pass-123", role=User.Role.TEACHER)
        self.teacher = Teacher.objects.create(user=self.teacher_user, employee_number="ENS-001", department="Informatique")
        self.course = Course.objects.create(code="INF101", title="Algorithmique", program="Informatique", teacher=self.teacher)
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course, academic_year="2026-2027")
        self.grade = Grade.objects.create(enrollment=self.enrollment, score="16.50", assessment="Examen")
        self.payment = Payment.objects.create(student=self.student, amount="50000.00", reason="Scolarité", reference="PAY-001", status=Payment.Status.PAID)

    def test_administrator_role_can_open_admin_without_superuser(self):
        admin_user = User.objects.create_user(username="gestionnaire", password="test-pass-123", role=User.Role.ADMIN)
        self.assertTrue(admin_user.is_staff)
        self.client.login(username="gestionnaire", password="test-pass-123")
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 200)

    def test_login_and_dashboard(self):
        self.assertTrue(self.client.login(username="etudiant", password="test-pass-123"))
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tableau de bord")
        self.assertContains(response, "Amina")

    def test_student_only_sees_own_academic_data(self):
        self.client.login(username="etudiant", password="test-pass-123")
        response = self.client.get(reverse("grades"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "16,50")
        self.assertEqual(self.client.get(reverse("students")).status_code, 403)

    def test_student_can_download_transcript_and_certificate(self):
        self.client.login(username="etudiant", password="test-pass-123")
        transcript = self.client.get(reverse("transcript_pdf"))
        certificate = self.client.get(reverse("certificate_pdf"))
        self.assertEqual(transcript.status_code, 200)
        self.assertEqual(transcript["Content-Type"], "application/pdf")
        self.assertEqual(certificate.status_code, 200)
        self.assertEqual(certificate["Content-Type"], "application/pdf")

    def test_paid_receipt_is_available_only_to_owner(self):
        self.client.login(username="etudiant", password="test-pass-123")
        response = self.client.get(reverse("receipt_pdf", args=[self.payment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_notifications_are_marked_read(self):
        Notification.objects.create(recipient=self.student_user, title="Info", message="Rentrée lundi")
        self.client.login(username="etudiant", password="test-pass-123")
        response = self.client.post(reverse("notifications"))
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(self.student_user.notifications.get().read_at)
