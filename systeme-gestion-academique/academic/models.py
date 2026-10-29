from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
import re


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Administrateur"
        TEACHER = "TEACHER", "Enseignant"
        STUDENT = "STUDENT", "Étudiant"

    role = models.CharField(max_length=12, choices=Role.choices, default=Role.STUDENT)

    def save(self, *args, **kwargs):
        self.is_staff = self.is_superuser or self.role == self.Role.ADMIN
        super().save(*args, **kwargs)


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    student_number = models.CharField(max_length=30, unique=True)
    program = models.CharField(max_length=120)
    enrollment_date = models.DateField(default=timezone.localdate)
    active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        if self.user_id and self.user.role != User.Role.STUDENT:
            raise ValidationError({"user": "Le compte associé doit avoir le rôle Étudiant."})
        if self.enrollment_date and self.enrollment_date > timezone.localdate():
            raise ValidationError({"enrollment_date": "La date d'inscription ne peut pas être dans le futur."})

    def __str__(self):
        return f"{self.student_number} — {self.user.get_full_name() or self.user.username}"


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher_profile")
    employee_number = models.CharField(max_length=30, unique=True)
    department = models.CharField(max_length=120)

    def clean(self):
        super().clean()
        if self.user_id and self.user.role != User.Role.TEACHER:
            raise ValidationError({"user": "Le compte associé doit avoir le rôle Enseignant."})

    def __str__(self):
        return f"{self.employee_number} — {self.user.get_full_name() or self.user.username}"


class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=150)
    program = models.CharField(max_length=120)
    credits = models.PositiveSmallIntegerField(default=3)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(credits__gte=1) & Q(credits__lte=60), name="course_credits_1_60"),
        ]

    def clean(self):
        super().clean()
        if self.credits is not None and not 1 <= self.credits <= 60:
            raise ValidationError({"credits": "Le nombre de crédits doit être compris entre 1 et 60."})

    def __str__(self):
        return f"{self.code} — {self.title}"


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    academic_year = models.CharField(max_length=9, default="2026-2027")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "course", "academic_year"], name="unique_student_course_year"),
        ]

    def clean(self):
        super().clean()
        if self.academic_year and not re.fullmatch(r"(19|20|21)\d{2}-(19|20|21)\d{2}", self.academic_year):
            raise ValidationError({"academic_year": "Format attendu : AAAA-AAAA, par exemple 2026-2027."})
        if self.academic_year:
            start, end = map(int, self.academic_year.split("-"))
            if end != start + 1:
                raise ValidationError({"academic_year": "L'année académique doit couvrir deux années consécutives."})
        if self.student_id and self.course_id:
            if not self.student.active:
                raise ValidationError({"student": "Un étudiant inactif ne peut pas être inscrit à un cours."})
            if self.student.program.strip().casefold() != self.course.program.strip().casefold():
                raise ValidationError({"course": "Le cours doit appartenir à la même formation que l'étudiant."})

    def __str__(self):
        return f"{self.student} / {self.course}"


class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="grades")
    score = models.DecimalField(max_digits=5, decimal_places=2)
    assessment = models.CharField(max_length=80, default="Examen")
    recorded_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["enrollment__course__code"]
        constraints = [
            models.CheckConstraint(condition=Q(score__gte=0) & Q(score__lte=20), name="grade_score_0_20"),
            models.UniqueConstraint(fields=["enrollment", "assessment"], name="unique_assessment_per_enrollment"),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.score is not None and not 0 <= self.score <= 20:
            errors["score"] = "La note doit être comprise entre 0 et 20."
        if self.enrollment_id and not self.enrollment.student.active:
            errors["enrollment"] = "Impossible de saisir une note pour un étudiant inactif."
        if errors:
            raise ValidationError(errors)

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

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="payment_amount_positive"),
        ]

    def clean(self):
        super().clean()
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Le montant du paiement doit être supérieur à zéro."})
        if self.status == self.Status.PAID and not self.paid_at:
            self.paid_at = timezone.now()
        elif self.status != self.Status.PAID:
            self.paid_at = None

    def save(self, *args, **kwargs):
        if self.status == self.Status.PAID and not self.paid_at:
            self.paid_at = timezone.now()
        elif self.status != self.Status.PAID:
            self.paid_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} — {self.amount}"


class Schedule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sessions")
    weekday = models.CharField(max_length=12, choices=[
        ("Lundi", "Lundi"), ("Mardi", "Mardi"), ("Mercredi", "Mercredi"),
        ("Jeudi", "Jeudi"), ("Vendredi", "Vendredi"), ("Samedi", "Samedi")])
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=40)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(end_time__gt=F("start_time")), name="schedule_end_after_start"),
        ]

    def clean(self):
        super().clean()
        errors = {}
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            errors["end_time"] = "L'heure de fin doit être postérieure à l'heure de début."
        if self.course_id and self.weekday and self.start_time and self.end_time and self.end_time > self.start_time:
            conflicts = Schedule.objects.filter(weekday=self.weekday).filter(
                start_time__lt=self.end_time, end_time__gt=self.start_time
            ).exclude(pk=self.pk)
            room_conflict = conflicts.filter(room__iexact=self.room)
            teacher_id = self.course.teacher_id
            teacher_conflict = conflicts.filter(course__teacher_id=teacher_id) if teacher_id else Schedule.objects.none()
            course_conflict = conflicts.filter(course_id=self.course_id)
            if room_conflict.exists():
                errors["room"] = "Cette salle est déjà réservée sur ce créneau."
            if teacher_conflict.exists():
                errors["course"] = "L'enseignant est déjà affecté à un autre cours sur ce créneau."
            if course_conflict.exists():
                errors["course"] = "Ce cours possède déjà une séance qui chevauche ce créneau."
        if errors:
            raise ValidationError(errors)

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
