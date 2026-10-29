from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from .forms import EnrollmentForm, GradeForm, ScheduleForm, PaymentForm
from .models import User, Student, Teacher, Course, Enrollment, Grade, Payment, Notification, Schedule


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
        self.assertEqual(self.client.get(reverse("student_create")).status_code, 403)

    def test_student_can_download_transcript_and_certificate(self):
        self.client.login(username="etudiant", password="test-pass-123")
        transcript = self.client.get(reverse("transcript_pdf"))
        certificate = self.client.get(reverse("certificate_pdf"))
        self.assertEqual(transcript.status_code, 200)
        self.assertEqual(transcript["Content-Type"], "application/pdf")
        self.assertEqual(certificate.status_code, 200)
        self.assertEqual(certificate["Content-Type"], "application/pdf")

    def test_inactive_student_cannot_get_certificate(self):
        self.student.active = False
        self.student.save()
        self.client.login(username="etudiant", password="test-pass-123")
        self.assertEqual(self.client.get(reverse("certificate_pdf")).status_code, 403)

    def test_paid_receipt_is_available_only_to_owner(self):
        self.client.login(username="etudiant", password="test-pass-123")
        response = self.client.get(reverse("receipt_pdf", args=[self.payment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        other_user = User.objects.create_user(username="etudiant2", password="test-pass-123", role=User.Role.STUDENT)
        Student.objects.create(user=other_user, student_number="ETU-002", program="Informatique")
        self.client.login(username="etudiant2", password="test-pass-123")
        self.assertEqual(self.client.get(reverse("receipt_pdf", args=[self.payment.pk])).status_code, 403)

    def test_notifications_are_marked_read(self):
        Notification.objects.create(recipient=self.student_user, title="Info", message="Rentrée lundi")
        self.client.login(username="etudiant", password="test-pass-123")
        response = self.client.post(reverse("notifications"))
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(self.student_user.notifications.get().read_at)

    def test_enrollment_rejects_nonconsecutive_year_and_wrong_program(self):
        wrong_year = EnrollmentForm(data={"student": self.student.pk, "course": self.course.pk, "academic_year": "2026-2028"})
        self.assertFalse(wrong_year.is_valid())
        other_course = Course.objects.create(code="MATH101", title="Mathématiques", program="Mathématiques", teacher=self.teacher)
        wrong_program = EnrollmentForm(data={"student": self.student.pk, "course": other_course.pk, "academic_year": "2026-2027"})
        self.assertFalse(wrong_program.is_valid())
        self.assertIn("course", wrong_program.errors)

    def test_grade_form_rejects_score_outside_twenty(self):
        form = GradeForm(data={"enrollment": self.enrollment.pk, "assessment": "Contrôle", "score": "21"})
        self.assertFalse(form.is_valid())
        self.assertIn("score", form.errors)

    def test_payment_form_rejects_zero_amount(self):
        form = PaymentForm(data={"student": self.student.pk, "amount": "0", "reason": "Scolarité", "status": "PENDING", "reference": "PAY-002"})
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_schedule_rejects_end_before_start(self):
        form = ScheduleForm(data={"course": self.course.pk, "weekday": "Lundi", "start_time": "10:00", "end_time": "09:00", "room": "A1"})
        self.assertFalse(form.is_valid())
        self.assertIn("end_time", form.errors)

    def test_schedule_rejects_room_overlap(self):
        Schedule.objects.create(course=self.course, weekday="Lundi", start_time="09:00", end_time="11:00", room="A1")
        other_course = Course.objects.create(code="INF102", title="Programmation", program="Informatique", teacher=self.teacher)
        form = ScheduleForm(data={"course": other_course.pk, "weekday": "Lundi", "start_time": "10:00", "end_time": "12:00", "room": "a1"})
        self.assertFalse(form.is_valid())
        self.assertIn("room", form.errors)

    def test_teacher_cannot_edit_another_teachers_grade(self):
        other_teacher_user = User.objects.create_user(username="enseignant2", password="test-pass-123", role=User.Role.TEACHER)
        other_teacher = Teacher.objects.create(user=other_teacher_user, employee_number="ENS-002", department="Mathématiques")
        other_course = Course.objects.create(code="MAT101", title="Mathématiques", program="Informatique", teacher=other_teacher)
        other_enrollment = Enrollment.objects.create(student=self.student, course=other_course, academic_year="2026-2027")
        other_grade = Grade.objects.create(enrollment=other_enrollment, score="12.00", assessment="Devoir")
        self.client.login(username="enseignant", password="test-pass-123")
        self.assertEqual(self.client.get(reverse("grade_edit", args=[other_grade.pk])).status_code, 403)

    def test_payment_paid_at_is_set_automatically(self):
        self.assertIsNotNone(self.payment.paid_at)
