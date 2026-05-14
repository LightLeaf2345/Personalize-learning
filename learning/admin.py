# learning/admin.py
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Question, VocabularyItem, UserProfile, Attempt, Lesson 

@admin.register(Question)
class QuestionAdmin(ImportExportModelAdmin):
    list_display = ("id", "category", "sub_category", "difficulty")
    list_filter = ("category", "difficulty", "sub_category")
    search_fields = ("question_text",)

@admin.register(Lesson)
class LessonAdmin(ImportExportModelAdmin): 
    list_display = ("title", "level", "order_num")
    list_filter = ("level",)
    search_fields = ("title",)

@admin.register(VocabularyItem)
class VocabAdmin(ImportExportModelAdmin):
    list_display = ("word", "difficulty")

@admin.register(UserProfile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "level", "last_active")

@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "correct", "timestamp")