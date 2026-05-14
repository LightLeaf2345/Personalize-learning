from django.urls import path
from . import views

app_name = "learning"

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"), 
    path("api/get_question/", views.get_question, name="get_question"),
    path("api/check_answer/", views.check_answer, name="check_answer"),
    path("api/get_ai_help/", views.get_ai_help, name="get_ai_help"),
    path("api/get_explanation/", views.get_explanation, name="get_explanation"),
    path('curriculum/', views.curriculum_view, name='curriculum'),
    path('api/lesson/<int:lesson_id>/', views.get_lesson_api, name='get_lesson_api'),
]