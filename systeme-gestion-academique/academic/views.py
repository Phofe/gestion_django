from functools import wraps
from io import BytesIO
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .models import Student, Teacher, Course, Grade, Payment, Schedule, Notification, User

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
    else:
        grade_qs = Grade.objects.all()
        payment_qs = Payment.objects.all()
        schedule_qs = Schedule.objects.all()
    context = {
        "role_label": request.user.get_role_display(),
        "student_count": Student.objects.count() if role == User.Role.ADMIN or request.user.is_superuser else None,
        "teacher_count": Teacher.objects.count() if role == User.Role.ADMIN or request.user.is_superuser else None,
        "course_count": Course.objects.count(),
        "grade_count": grade_qs.count(),
        "payment_count": payment_qs.count(),
        "schedule_count": schedule_qs.count(),
        "unread_count": request.user.notifications.filter(read_at__isnull=True).count(),
        "recent_notifications": request.user.notifications.all()[:5],
    }
    return render(request, "academic/dashboard.html", context)

@role_required(User.Role.ADMIN)
def students(request):
    return render(request, "academic/list.html", {"title": "Étudiants", "items": visible_student(request.user), "columns": ["student_number", "program", "enrollment_date", "active"], "admin_link": "/admin/academic/student/"})

@role_required(User.Role.ADMIN)
def teachers(request):
    return render(request, "academic/list.html", {"title": "Enseignants", "items": Teacher.objects.select_related("user"), "columns": ["employee_number", "department"], "admin_link": "/admin/academic/teacher/"})

@login_required
def courses(request):
    items = Course.objects.select_related("teacher__user")
    if request.user.role == User.Role.STUDENT:
        items = items.filter(enrollments__student__user=request.user)
    elif request.user.role == User.Role.TEACHER:
        items = items.filter(teacher__user=request.user)
    return render(request, "academic/list.html", {"title": "Cours", "items": items.distinct(), "columns": ["code", "title", "program", "credits"], "admin_link": "/admin/academic/course/" if request.user.role == User.Role.ADMIN or request.user.is_superuser else None})

@login_required
def grades(request):
    items = Grade.objects.select_related("enrollment__student__user", "enrollment__course")
    if request.user.role == User.Role.STUDENT:
        items = items.filter(enrollment__student__user=request.user)
    elif request.user.role == User.Role.TEACHER:
        items = items.filter(enrollment__course__teacher__user=request.user)
    return render(request, "academic/list.html", {"title": "Notes", "items": items, "columns": ["enrollment", "assessment", "score", "recorded_at"], "admin_link": "/admin/academic/grade/" if request.user.role in [User.Role.ADMIN, User.Role.TEACHER] or request.user.is_superuser else None})

@login_required
def payments(request):
    items = Payment.objects.select_related("student__user")
    if request.user.role == User.Role.STUDENT:
        items = items.filter(student__user=request.user)
    elif request.user.role == User.Role.TEACHER:
        items = Payment.objects.none()
    return render(request, "academic/list.html", {"title": "Paiements", "items": items, "columns": ["reference", "student", "amount", "status", "created_at"], "admin_link": "/admin/academic/payment/" if request.user.role == User.Role.ADMIN or request.user.is_superuser else None})

@login_required
def schedules(request):
    items = Schedule.objects.select_related("course")
    if request.user.role == User.Role.STUDENT:
        items = items.filter(course__enrollments__student__user=request.user)
    elif request.user.role == User.Role.TEACHER:
        items = items.filter(course__teacher__user=request.user)
    return render(request, "academic/list.html", {"title": "Emplois du temps", "items": items.distinct(), "columns": ["course", "weekday", "start_time", "end_time", "room"], "admin_link": "/admin/academic/schedule/" if request.user.role == User.Role.ADMIN or request.user.is_superuser else None})

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
    elif request.user.role in [User.Role.ADMIN, User.Role.TEACHER] or request.user.is_superuser:
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
