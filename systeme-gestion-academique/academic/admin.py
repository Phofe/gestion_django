from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Student, Teacher, Course, Enrollment, Grade, Payment, Schedule, Notification

@admin.register(User)
class AcademicUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Profil académique", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Profil académique", {"fields": ("role",)}),)
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active")

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_number", "user", "program", "active")
    search_fields = ("student_number", "user__username", "user__last_name", "program")

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("employee_number", "user", "department")
    search_fields = ("employee_number", "user__last_name", "department")

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "program", "credits", "teacher")
    search_fields = ("code", "title", "program")

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "academic_year")
    list_filter = ("academic_year", "course__program")

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "assessment", "score", "recorded_at")
    list_filter = ("assessment",)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "student", "amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("reference", "student__student_number")

admin.site.register(Schedule)
admin.site.register(Notification)
