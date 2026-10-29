from django import forms
from django.core.exceptions import ValidationError
from .models import User, Student, Teacher, Course, Enrollment, Grade, Payment, Schedule


class StyledModelForm(forms.ModelForm):
    """Ajoute des classes CSS communes aux formulaires métier."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "check-input")
            else:
                field.widget.attrs.setdefault("class", "form-control")
                field.widget.attrs.setdefault("autocomplete", "off")


class StudentForm(StyledModelForm):
    class Meta:
        model = Student
        fields = ["user", "student_number", "program", "enrollment_date", "active"]
        widgets = {"enrollment_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.filter(role=User.Role.STUDENT).order_by("username")


class TeacherForm(StyledModelForm):
    class Meta:
        model = Teacher
        fields = ["user", "employee_number", "department"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.filter(role=User.Role.TEACHER).order_by("username")


class CourseForm(StyledModelForm):
    class Meta:
        model = Course
        fields = ["code", "title", "program", "credits", "teacher"]
        widgets = {"credits": forms.NumberInput(attrs={"min": 1, "max": 60, "step": 1})}


class EnrollmentForm(StyledModelForm):
    class Meta:
        model = Enrollment
        fields = ["student", "course", "academic_year"]
        widgets = {"academic_year": forms.TextInput(attrs={"placeholder": "2026-2027", "pattern": r"(19|20|21)\d{2}-(19|20|21)\d{2}"})}

    def clean_academic_year(self):
        value = self.cleaned_data["academic_year"].strip()
        parts = value.split("-")
        if len(parts) != 2 or not all(part.isdigit() and len(part) == 4 for part in parts):
            raise ValidationError("Saisissez une année au format AAAA-AAAA.")
        if int(parts[1]) != int(parts[0]) + 1:
            raise ValidationError("Les deux années doivent être consécutives.")
        return value


class GradeForm(StyledModelForm):
    class Meta:
        model = Grade
        fields = ["enrollment", "assessment", "score"]
        widgets = {"score": forms.NumberInput(attrs={"min": 0, "max": 20, "step": "0.01"})}

    def __init__(self, *args, teacher=None, **kwargs):
        super().__init__(*args, **kwargs)
        if teacher is not None:
            self.fields["enrollment"].queryset = Enrollment.objects.filter(
                course__teacher=teacher, student__active=True
            ).select_related("student__user", "course").order_by("course__code", "student__student_number")

    def clean_assessment(self):
        value = self.cleaned_data["assessment"].strip()
        if not value:
            raise ValidationError("Le type d'évaluation est obligatoire.")
        return value


class PaymentForm(StyledModelForm):
    class Meta:
        model = Payment
        fields = ["student", "amount", "reason", "status", "reference"]
        widgets = {"amount": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"})}

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise ValidationError("Le montant doit être supérieur à zéro.")
        return amount


class ScheduleForm(StyledModelForm):
    class Meta:
        model = Schedule
        fields = ["course", "weekday", "start_time", "end_time", "room"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and end <= start:
            self.add_error("end_time", "L'heure de fin doit être postérieure à l'heure de début.")
        return cleaned
