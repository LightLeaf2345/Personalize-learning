# learning/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Question

class QuestionCreateForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["question_text", "category", "sub_category", "difficulty", "options", "correct_answer", "explanation"]
        widgets = {
            "options": forms.Textarea(attrs={"rows":3, "placeholder":"Enter JSON list or leave blank"}),
        }

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    # Điều kiện: email không được trùng
    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email đã được sử dụng.")
        return email

    # Điều kiện: username tối thiểu 4 ký tự
    def clean_username(self):
        username = self.cleaned_data["username"]
        if len(username) < 4:
            raise forms.ValidationError("Tên đăng nhập phải ít nhất 4 ký tự.")
        return username

    # Điều kiện: email phải là email thật (định dạng chuẩn)
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data