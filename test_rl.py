import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from learning.rl_agent import ReinforcementLearningAgent
from learning.models import UserProfile, Question, Attempt

def test_rl_agent():
    print("🚀 Testing RL Agent...")

    # Create or get test user
    user, created = User.objects.get_or_create(username='test_user', defaults={'email': 'test@example.com'})
    if created:
        user.set_password('password')
        user.save()
        print("✅ Created test user")

    # Get or create profile
    profile, _ = UserProfile.objects.get_or_create(user=user)
    print(f"✅ User profile: Level {profile.level}, XP {profile.xp}")

    # Create RL agent
    agent = ReinforcementLearningAgent(user)
    print("✅ RL Agent initialized")

    # Test choose_action
    action = agent.choose_action()
    print(f"✅ Chosen action: {action}")

    # Test get_recommendation
    rec = agent.get_recommendation()
    print(f"✅ Recommendation: {rec}")

    # Test observe_feedback (simulate)
    # First, create a dummy question
    question, _ = Question.objects.get_or_create(
        question_text="What is the capital of France?",
        defaults={
            'category': 'vocabulary',
            'sub_category': 'geography',
            'difficulty': 1,
            'correct_answer': 'Paris'
        }
    )

    # Simulate correct answer
    reward = agent.observe_feedback(
        question={'sub_category': 'geography'},
        is_correct=True,
        action=action
    )
    print(f"✅ Feedback reward: {reward}")
    profile.refresh_from_db()  # Reload from DB
    print(f"✅ Updated profile: Level {profile.level}, XP {profile.xp}")

    # Test again
    action2 = agent.choose_action()
    print(f"✅ Second action: {action2}")

    # Simulate wrong answer
    reward2 = agent.observe_feedback(
        question={'sub_category': 'geography'},
        is_correct=False,
        action=action2
    )
    print(f"✅ Second feedback reward: {reward2}")
    profile.refresh_from_db()
    print(f"✅ Final profile: Level {profile.level}, XP {profile.xp}")

    print("✅ RL Agent test completed successfully!")

if __name__ == "__main__":
    test_rl_agent()