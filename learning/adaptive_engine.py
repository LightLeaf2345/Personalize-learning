# learning/adaptive_engine.py
from typing import Optional, List
from .models import Question, UserProfile
from django.utils import timezone
from datetime import timedelta
import random

class AdaptiveEngine:
    """
    Simple adaptive selection:
    - Prefer questions at user's level.
    - Prioritize user's weak_areas (sub_category).
    - Avoid recent questions (last 7 days).
    """

    def __init__(self, user):
        self.user = user
        self.profile, _ = UserProfile.objects.get_or_create(user=user)

    def _recent_question_ids(self, days: int = 7) -> List[int]:
        cutoff = timezone.now() - timedelta(days=days)
        return list(self.user.attempts.filter(timestamp__gte=cutoff).values_list("question_id", flat=True))

    def select_question(self, category: str = "grammar") -> Optional[Question]:
        qs = Question.objects.filter(category=category)
        if not qs.exists():
            return None

        recent_ids = set(self._recent_question_ids(7))
        weak_areas = self.profile.weak_areas or []

        # 1) weak area & exact level
        if weak_areas:
            candidates = qs.filter(sub_category__in=weak_areas, difficulty=self.profile.level)
            candidates = [q for q in candidates if q.id not in recent_ids]
            if candidates:
                return random.choice(candidates)

        # 2) same level (exclude recent)
        level_qs = qs.filter(difficulty=self.profile.level)
        level_candidates = [q for q in level_qs if q.id not in recent_ids]
        if level_candidates:
            return random.choice(level_candidates)
        if level_qs.exists():
            return random.choice(list(level_qs))

        # 3) neighbor levels
        neighbor_qs = qs.filter(difficulty__in=[max(1, self.profile.level - 1), min(3, self.profile.level + 1)])
        neighbor_candidates = [q for q in neighbor_qs if q.id not in recent_ids]
        if neighbor_candidates:
            return random.choice(neighbor_candidates)
        if neighbor_qs.exists():
            return random.choice(list(neighbor_qs))

        # 4) fallback random
        return qs.order_by("?").first()
