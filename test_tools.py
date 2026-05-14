import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from utils.ai_engine import init_knowledge_base, get_learning_support, search_related_courses, generate_learning_path, web_learning_search, translate_text

def test_tools():
    print("🚀 Testing AI Tools...")

    # Initialize knowledge base
    print("📚 Initializing knowledge base...")
    try:
        init_knowledge_base()
        print("✅ Knowledge base initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing knowledge base: {e}")

    # Test get_learning_support
    print("\n🧠 Testing get_learning_support...")
    try:
        result = get_learning_support(query="Làm thế nào để học tiếng Anh hiệu quả?")
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test generate_learning_path
    print("\n📚 Testing generate_learning_path...")
    try:
        result = generate_learning_path(user_level=1, weak_areas=["grammar", "vocabulary"])
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test web_learning_search (but it requires SerpAPI key)
    print("\n🌐 Testing web_learning_search...")
    try:
        result = web_learning_search(query="how to learn English")
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test translate_text (requires Gemini, but quota exceeded)
    print("\n🌍 Testing translate_text...")
    try:
        result = translate_text(text="Hello world", target_lang="vi")
        print(f"✅ Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_tools()