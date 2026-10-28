from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrateur"
        TEACHER = "TEACHER", "Enseignant"
        STUDENT = "STUDENT", "Étudiant"
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.STUDENT)

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    student_number = models.CharField(max_length=30, unique=True)
    program = models.CharField(max_length=120)
    enrollment_date = models.DateField(default=timezone.localdate)
    active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.student_number} — {self.user.get_full_name() or self.user.username}"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    employee_number = models.CharField(max_length=30, unique=True)
    department = models.CharField(max_length=120)
    def __str__(self):
        return f"{self.employee_number} — {self.user.get_full_name() or self.user.username}"

class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=150)
    program = models.CharField(max_length=120)
    credits = models.PositiveSmallIntegerField(default=3)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses")
    def __str__(self):
        return f"{self.code} — {self.title}"

class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    academic_year = models.CharField(max_length=9, default="2026-2027")
    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "course", "academic_year"], name="unique_student_course_year")]
    def __str__(self):
        return f"{self.student} / {self.course}"

class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="grades")
    score = models.DecimalField(max_digits=5, decimal_places=2)
    assessment = models.CharField(max_length=80, default="Examen")
    recorded_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["enrollment__course__code"]
    def __str__(self):
        return f"{self.enrollment} : {self.score}/20"

class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        PAID = "PAID", "Payé"
        CANCELLED = "CANCELLED", "Annulé"
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=150, default="Frais de scolarité")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    reference = models.CharField(max_length=50, unique=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.reference} — {self.amount}"

class Schedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sessions")
    weekday = models.CharField(max_length=12, choices=[
        ("Lundi","Lundi"),("Mardi","Mardi"),("Mercredi","Mercredi"),
        ("Jeudi","Jeudi"),("Vendredi","Vendredi"),("Samedi","Samedi")])
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=40)
    def __str__(self):
        return f"{self.course} — {self.weekday} {self.start_time}"

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=120)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ["-created_at"]
    def __str__(self):
        return f"{self.recipient}: {self.title}"
