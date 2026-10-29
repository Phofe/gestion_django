from functools import wraps
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .forms import StudentForm, TeacherForm, CourseForm, EnrollmentForm, GradeForm, PaymentForm, ScheduleForm
from .models import Student, Teacher, Course, Enrollment, Grade, Payment, Schedule, Notification, User


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(request, *args, **kwargs):
            if request.user.is_superuser or request.user.role in roles:
                return view(request, *args, **kwargs)
            return HttpResponseForbidden("Accès non autorisé pour ce profil.")
        return wrapped
    return decorator


def visible_student(user):
    if user.is_superuser or user.role == User.Role.ADMIN:
        return Student.objects.all()
    if user.role == User.Role.STUDENT:
        return Student.objects.filter(user=user)
    return Student.objects.none()


@login_required
def dashboard(request):
    role = request.user.role
    student_profile = getattr(request.user, "student_profile", None)
    teacher_profile = getattr(request.user, "teacher_profile", None)
    if role == User.Role.STUDENT and student_profile:
        grade_qs = Grade.objects.filter(enrollment__student=student_profile)
        payment_qs = Payment.objects.filter(student=student_profile)
        schedule_qs = Schedule.objects.filter(course__enrollments__student=student_profile).distinct()
    elif role == User.Role.TEACHER and teacher_profile:
        grade_qs = Grade.objects.filter(enrollment__course__teacher=teacher_profile)
        payment_qs = Payment.objects.none()
        schedule_qs = Schedule.objects.filter(course__teacher=teacher_profile)
    elif role == User.Role.ADMIN or request.user.is_superuser:
        grade_qs = Grade.objects.all()
        payment_qs = Payment.objects.all()
        schedule_qs = Schedule.objects.all()
    else:
        grade_qs = Grade.objects.none()
        payment_qs = Payment.objects.none()
        schedule_qs = Schedule.objects.none()
    context = {
        "role_label": request.user.get_role_display(),
        "student_count": Student.objects.count() if role == User.Role.ADMIN or request.user.is_superuser else None,
        "teacher_count": Teacher.objects.count() if role == User.Role.ADMIN or request.user.is_superuser else None,
        "course_count": Course.objects.count() if role == User.Role.ADMIN or request.user.is_superuser else Course.objects.filter(
            enrollments__student__user=request.user
        ).count() if role == User.Role.STUDENT else Course.objects.filter(teacher__user=request.user).count() if role == User.Role.TEACHER else 0,
        "grade_count": grade_qs.count(),
        "payment_count": payment_qs.count(),
        "schedule_count": schedule_qs.count(),
        "unread_count": request.user.notifications.filter(read_at__isnull=True).count(),
        "recent_notifications": request.user.notifications.all()[:5],
    }
    return render(request, "academic/dashboard.html", context)


def _business_form(request, form_class, title, success_url, instance=None, **form_kwargs):
    is_edit = instance is not None
    if request.method == "POST":
        form = form_class(request.POST, instance=instance, **form_kwargs)
        if form.is_valid():
            try:
                with transaction.atomic():
                    saved = form.save(commit=False)
                    saved.full_clean()
                    saved.save()
                messages.success(request, f"{title} enregistré avec succès.")
                return redirect(success_url)
            except ValidationError as exc:
                if hasattr(exc, "message_dict"):
                    for field, errors in exc.message_dict.items():
                        for error in errors:
                            form.add_error(field if field in form.fields else None, error)
                else:
                    form.add_error(None, "; ".join(exc.messages))
            except IntegrityError:
                form.add_error(None, "Cette opération crée un doublon ou enfreint une règle de gestion.")
    else:
        form = form_class(instance=instance, **form_kwargs)
    return render(request, "academic/form.html", {
        "form": form, "title": title, "is_edit": is_edit,
        "cancel_url": success_url,
    })


@role_required(User.Role.ADMIN)
def students(request):
    return render(request, "academic/list.html", {
        "title": "Étudiants", "items": Student.objects.select_related("user"),
        "columns": ["student_number", "user", "program", "enrollment_date", "active"],
        "create_url_name": "student_create", "edit_url_name": "student_edit", "can_manage": True,
        "admin_link": "/admin/academic/student/",
    })


@role_required(User.Role.ADMIN)
def student_create(request):
    return _business_form(request, StudentForm, "Créer un étudiant", "students")


@role_required(User.Role.ADMIN)
def student_edit(request, object_id):
    instance = get_object_or_404(Student, pk=object_id)
    return _business_form(request, StudentForm, "Modifier un étudiant", "students", instance)


@role_required(User.Role.ADMIN)
def teachers(request):
    return render(request, "academic/list.html", {
        "title": "Enseignants", "items": Teacher.objects.select_related("user"),
        "columns": ["employee_number", "user", "department"],
        "create_url_name": "teacher_create", "edit_url_name": "teacher_edit", "can_manage": True,
        "admin_link": "/admin/academic/teacher/",
    })


@role_required(User.Role.ADMIN)
def teacher_create(request):
    return _business_form(request, TeacherForm, "Créer un enseignant", "teachers")


@role_required(User.Role.ADMIN)
def teacher_edit(request, object_id):
    instance = get_object_or_404(Teacher, pk=object_id)
    return _business_form(request, TeacherForm, "Modifier un enseignant", "teachers", instance)


@login_required
def courses(request):
    items = Course.objects.select_related("teacher__user")
    can_manage = request.user.is_superuser or request.user.role == User.Role.ADMIN
    if request.user.role == User.Role.STUDENT:
        items = items.filter(enrollments__student__user=request.user)
    elif request.user.role == User.Role.TEACHER:
        items = items.filter(teacher__user=request.user)
    return render(request, "academic/list.html", {
        "title": "Cours", "items": items.distinct(),
        "columns": ["code", "title", "program", "credits", "teacher"],
        "create_url_name": "course_create" if can_manage else None,
        "edit_url_name": "course_edit" if can_manage else None, "can_manage": can_manage,
        "admin_link": "/admin/academic/course/" if can_manage else None,
    })


@role_required(User.Role.ADMIN)
def course_create(request):
    return _business_form(request, CourseForm, "Créer un cours", "courses")


@role_required(User.Role.ADMIN)
def course_edit(request, object_id):
    instance = get_object_or_404(Course, pk=object_id)
    return _business_form(request, CourseForm, "Modifier un cours", "courses", instance)


@role_required(User.Role.ADMIN)
def enrollments(request):
    return render(request, "academic/list.html", {
        "title": "Inscriptions", "items": Enrollment.objects.select_related("student__user", "course"),
        "columns": ["student", "course", "academic_year"],
        "create_url_name": "enrollment_create", "edit_url_name": "enrollment_edit", "can_manage": True,
    })


@role_required(User.Role.ADMIN)
def enrollment_create(request):
    return _business_form(request, EnrollmentForm, "Inscrire un étudiant", "enrollments")


@role_required(User.Role.ADMIN)
def enrollment_edit(request, object_id):
    instance = get_object_or_404(Enrollment, pk=object_id)
    return _business_form(request, EnrollmentForm, "Modifier une inscription", "enrollments", instance)


@login_required
def grades(request):
    items = Grade.objects.select_related("enrollment__student__user", "enrollment__course")
    can_manage = request.user.is_superuser or request.user.role == User.Role.ADMIN
    if request.user.role == User.Role.STUDENT:
        items = items.filter(enrollment__student__user=request.user)
    elif request.user.role == User.Role.TEACHER:
        items = items.filter(enrollment__course__teacher__user=request.user)
        can_manage = bool(getattr(request.user, "teacher_profile", None))
    else:
        can_manage = can_manage
    return render(request, "academic/list.html", {
        "title": "Notes", "items": items,
        "columns": ["enrollment", "assessment", "score", "recorded_at"],
        "create_url_name": "grade_create" if can_manage else None,
        "edit_url_name": "grade_edit" if can_manage else None, "can_manage": can_manage,
        "admin_link": "/admin/academic/grade/" if request.user.role == User.Role.ADMIN or request.user.is_superuser else None,
    })


@login_required
def grade_create(request):
    teacher = None
    if not (request.user.is_superuser or request.user.role == User.Role.ADMIN):
        if request.user.role != User.Role.TEACHER or not hasattr(request.user, "teacher_profile"):
            return HttpResponseForbidden("Seuls l'administration et les enseignants peuvent saisir des notes.")
        teacher = request.user.teacher_profile
    return _business_form(request, GradeForm, "Saisir une note", "grades", teacher=teacher)


@login_required
def grade_edit(request, object_id):
    instance = get_object_or_404(Grade.objects.select_related("enrollment__course__teacher"), pk=object_id)
    teacher = None
    if not (request.user.is_superuser or request.user.role == User.Role.ADMIN):
        if request.user.role != User.Role.TEACHER or not hasattr(request.user, "teacher_profile"):
            return HttpResponseForbidden("Modification de note non autorisée.")
        teacher = request.user.teacher_profile
        if instance.enrollment.course.teacher_id != teacher.pk:
            return HttpResponseForbidden("Vous ne pouvez modifier que les notes de vos cours.")
    return _business_form(request, GradeForm, "Modifier une note", "grades", instance, teacher=teacher)


@role_required(User.Role.ADMIN)
def payments(request):
    return render(request, "academic/list.html", {
        "title": "Paiements", "items": Payment.objects.select_related("student__user"),
        "columns": ["reference", "student", "amount", "status", "created_at"],
        "create_url_name": "payment_create", "edit_url_name": "payment_edit", "can_manage": True,
        "admin_link": "/admin/academic/payment/",
    })


@role_required(User.Role.ADMIN)
def payment_create(request):
    return _business_form(request, PaymentForm, "Enregistrer un paiement", "payments")


@role_required(User.Role.ADMIN)
def payment_edit(request, object_id):
    instance = get_object_or_404(Payment, pk=object_id)
    return _business_form(request, PaymentForm, "Modifier un paiement", "payments", instance)


@login_required
def schedules(request):
    items = Schedule.objects.select_related("course__teacher__user")
    can_manage = request.user.is_superuser or request.user.role == User.Role.ADMIN
    if request.user.role == User.Role.STUDENT:
        items = items.filter(course__enrollments__student__user=request.user)
    elif request.user.role == User.Role.TEACHER:
        items = items.filter(course__teacher__user=request.user)
    return render(request, "academic/list.html", {
        "title": "Emplois du temps", "items": items.distinct(),
        "columns": ["course", "weekday", "start_time", "end_time", "room"],
        "create_url_name": "schedule_create" if can_manage else None,
        "edit_url_name": "schedule_edit" if can_manage else None, "can_manage": can_manage,
        "admin_link": "/admin/academic/schedule/" if can_manage else None,
    })


@role_required(User.Role.ADMIN)
def schedule_create(request):
    return _business_form(request, ScheduleForm, "Créer une séance", "schedules")


@role_required(User.Role.ADMIN)
def schedule_edit(request, object_id):
    instance = get_object_or_404(Schedule, pk=object_id)
    return _business_form(request, ScheduleForm, "Modifier une séance", "schedules", instance)


@login_required
def notifications(request):
    qs = request.user.notifications.all()
    if request.method == "POST":
        qs.filter(read_at__isnull=True).update(read_at=timezone.now())
        messages.success(request, "Notifications marquées comme lues.")
        return redirect("notifications")
    return render(request, "academic/notifications.html", {"items": qs})


def pdf_response(title, lines, filename):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    pdf.setTitle(title)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(55, height - 60, title)
    pdf.setFont("Helvetica", 10)
    y = height - 100
    for line in lines:
        if y < 60:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = height - 60
        pdf.drawString(55, y, str(line)[:110])
        y -= 22
    pdf.setFont("Helvetica-Oblique", 8)
    pdf.drawString(55, 35, "Document généré par le MVP de démonstration — à valider avant usage officiel.")
    pdf.showPage()
    pdf.save()
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def transcript_pdf(request):
    profile = getattr(request.user, "student_profile", None)
    if request.user.role == User.Role.STUDENT and profile:
        qs = Grade.objects.filter(enrollment__student=profile).select_related("enrollment__course")
    elif request.user.role == User.Role.TEACHER and getattr(request.user, "teacher_profile", None):
        qs = Grade.objects.filter(enrollment__course__teacher=request.user.teacher_profile).select_related("enrollment__course")
    elif request.user.role == User.Role.ADMIN or request.user.is_superuser:
        qs = Grade.objects.select_related("enrollment__student__user", "enrollment__course")
        student_id = request.GET.get("student")
        if student_id:
            qs = qs.filter(enrollment__student_id=student_id)
    else:
        return HttpResponseForbidden("Accès non autorisé.")
    lines = [f"Compte : {request.user.get_full_name() or request.user.username}", f"Date : {timezone.localdate()}"]
    for grade in qs:
        lines.append(f"{grade.enrollment.course.code} — {grade.enrollment.course.title} | {grade.assessment} : {grade.score}/20")
    return pdf_response("Relevé de notes", lines, "releve-de-notes.pdf")


@login_required
def certificate_pdf(request):
    profile = getattr(request.user, "student_profile", None)
    if not profile and not (request.user.role == User.Role.ADMIN or request.user.is_superuser):
        return HttpResponseForbidden("Réservé à l'étudiant concerné ou à l'administration.")
    student = profile if profile else get_object_or_404(Student, pk=request.GET.get("student"))
    if not student.active:
        return HttpResponseForbidden("Une attestation ne peut être générée que pour un étudiant actif.")
    return pdf_response("Attestation de scolarité", [
        f"Nom : {student.user.get_full_name() or student.user.username}",
        f"Matricule : {student.student_number}", f"Formation : {student.program}",
        f"Inscription : {student.enrollment_date}", f"Statut actif : {'Oui' if student.active else 'Non'}",
    ], "attestation-scolarite.pdf")


@login_required
def receipt_pdf(request, payment_id):
    payment = get_object_or_404(Payment.objects.select_related("student__user"), pk=payment_id)
    if not (request.user.is_superuser or request.user.role == User.Role.ADMIN or (request.user.role == User.Role.STUDENT and payment.student.user_id == request.user.id)):
        return HttpResponseForbidden("Accès non autorisé à ce reçu.")
    if payment.status != Payment.Status.PAID:
        return HttpResponseForbidden("Le reçu est disponible uniquement pour un paiement confirmé.")
    return pdf_response("Reçu de paiement", [
        f"Référence : {payment.reference}", f"Étudiant : {payment.student}",
        f"Motif : {payment.reason}", f"Montant : {payment.amount}",
        f"Date de paiement : {payment.paid_at or payment.created_at}",
    ], f"recu-{payment.reference}.pdf")
