from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Student, Teacher, Course, Enrollment, Grade, Payment, Schedule, Notification

class AcademicRoleAdminMixin:
    def has_module_permission(self, request):
        return request.user.is_superuser or getattr(request.user, "role", None) == User.Role.ADMIN

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or getattr(request.user, "role", None) == User.Role.ADMIN

    def has_add_permission(self, request):
        return request.user.is_superuser or getattr(request.user, "role", None) == User.Role.ADMIN

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or getattr(request.user, "role", None) == User.Role.ADMIN

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or getattr(request.user, "role", None) == User.Role.ADMIN

@admin.register(User)
class AcademicUserAdmin(AcademicRoleAdminMixin, UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Profil académique", {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Profil académique", {"fields": ("role",)}),)
    list_display = ("username", "email", "first_name", "last_name", "role", "is_active")
    list_filter = ("role", "is_active")

@admin.register(Student)
class StudentAdmin(AcademicRoleAdminMixin, admin.ModelAdmin):
    list_display = ("student_number", "user", "program", "active")
    search_fields = ("student_number", "user__username", "user__last_name", "program")

@admin.register(Teacher)
class TeacherAdmin(AcademicRoleAdminMixin, admin.ModelAdmin):
    list_display = ("employee_number", "user", "department")
    search_fields = ("employee_number", "user__last_name", "department")

@admin.register(Course)
class CourseAdmin(AcademicRoleAdminMixin, admin.ModelAdmin):
    list_display = ("code", "title", "program", "credits", "teacher")
    search_fields = ("code", "title", "program")

@admin.register(Enrollment)
class EnrollmentAdmin(AcademicRoleAdminMixin, admin.ModelAdmin):
    list_display = ("student", "course", "academic_year")
    list_filter = ("academic_year", "course__program")

@admin.register(Grade)
class GradeAdmin(AcademicRoleAdminMixin, admin.ModelAdmin):
    list_display = ("enrollment", "assessment", "score", "recorded_at")
    list_filter = ("assessment",)

@admin.register(Payment)
class PaymentAdmin(AcademicRoleAdminMixin, admin.ModelAdmin):
    list_display = ("reference", "student", "amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("reference", "student__student_number")

@admin.register(Schedule)
class ScheduleAdmin(AcademicRoleAdminMixin, admin.ModelAdmin):
    list_display = ("course", "weekday", "start_time", "end_time", "room")

@admin.register(Notification)
class NotificationAdmin(AcademicRoleAdminMixin, admin.ModelAdmin):
    list_display = ("recipient", "title", "created_at", "read_at")
