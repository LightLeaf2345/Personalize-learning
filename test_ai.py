#!/usr/bin/env python
"""
Test script for AI Engine
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from utils.ai_engine import init_knowledge_base, agentic_graph

def test_ai_engine():
    print("🚀 Testing AI Engine...")

    # Initialize knowledge base
    print("📚 Initializing knowledge base...")
    init_knowledge_base()

    # Test queries
    test_queries = [
        "Làm thế nào để học tiếng Anh hiệu quả?",
        "Tôi muốn tìm khóa học cho người mới bắt đầu",
        "Làm thế nào để cải thiện phát âm?",
        "Tìm thông tin về phương pháp học từ vựng tiếng Anh"
    ]

    for query in test_queries:
        print(f"\n❓ Query: {query}")
        try:
            result = agentic_graph.invoke({
                "query": query,
                "last_agent_response": "",
                "last_agent": "",
                "tool_observations": [],
                "num_steps": 0
            })
            print(f"✅ Response: {result['last_agent_response']}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_ai_engine()