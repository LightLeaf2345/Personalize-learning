
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Question

@receiver(post_migrate)
def create_default_questions(sender, **kwargs):
    if sender.name != "learning":
        return  # chỉ chạy khi migrate app learning

    if Question.objects.exists():
        return  