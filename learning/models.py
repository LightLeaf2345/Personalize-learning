# learning/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

User = settings.AUTH_USER_MODEL

DIFFICULTY_CHOICES = (
    (1, "Beginner"),
    (2, "Intermediate"),
    (3, "Advanced"),
)

CATEGORY_CHOICES = (
    ("grammar", "Grammar"),
    ("vocabulary", "Vocabulary"),
    ("reading", "Reading"),
)

class Question(models.Model):
    question_text = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="grammar")
    sub_category = models.CharField(max_length=100, blank=True, default="")
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=1)
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.TextField()
    explanation = models.TextField(blank=True, default="")
    
    media_url = models.CharField(max_length=500, blank=True, null=True) 
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_difficulty_display()}] {self.question_text[:60]}"

class Lesson(models.Model):
    title = models.CharField(max_length=255)
    level = models.IntegerField(choices=DIFFICULTY_CHOICES, default=1)
    order_num = models.IntegerField(default=1)
    content_html = models.TextField()

    class Meta:
        ordering = ['level', 'order_num']

    def __str__(self):
        return f"[Level {self.level}] {self.title}"

class VocabularyItem(models.Model):
    word = models.CharField(max_length=200)
    meaning = models.TextField()
    example = models.TextField(blank=True)
    difficulty = models.IntegerField(choices=DIFFICULTY_CHOICES, default=1)

    def __str__(self):
        return self.word

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="learning_profile")
    level = models.IntegerField(choices=DIFFICULTY_CHOICES, default=1)
    xp = models.IntegerField(default=0) 
    
    # Knowledge Tracing (Chương 3)
    grammar_mastery = models.FloatField(default=0.1)
    vocab_mastery = models.FloatField(default=0.1)
    listening_mastery = models.FloatField(default=0.1)

    # Reinforcement Learning (Chương 4)
    q_policy = models.JSONField(default=dict, blank=True) 

    weak_areas = models.JSONField(default=list, blank=True)
    vocabulary_bank = models.JSONField(default=dict, blank=True)
    last_active = models.DateTimeField(default=timezone.now)

    def add_xp(self, amount):
        """
        Hàm cộng/trừ XP và tự động lưu để kích hoạt logic thăng cấp trong hàm save().
        """
        self.xp += amount
        # Đảm bảo XP không bị âm (để không lỗi logic)
        if self.xp < 0:
            self.xp = 0
        self.save() # Gọi save() để kích hoạt logic phân chia Level ở dưới

    def save(self, *args, **kwargs):
        """
        Logic phân cấp dựa trên XP.
        """
        if self.xp < 100:
            self.level = 1  # Beginner
        elif self.xp < 300:
            self.level = 2  # Intermediate
        else:
            self.level = 3  # Advanced
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} | XP: {self.xp}"

class Attempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attempts")
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True)
    selected_answer = models.TextField(blank=True)
    correct = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-timestamp",)

    def __str__(self):
        return f"Attempt(user={self.user.username}, q={self.question_id}, correct={self.correct})"

# [MỚI THÊM] Tự động tạo UserProfile khi có một User mới đăng ký
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)