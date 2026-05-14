#!/usr/bin/env python
"""
Debug AI Agent Tool Calling
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from utils.ai_engine import agentic_graph, AgentState

def debug_agent():
    print("🔍 Debug AI Agent Tool Calling...")

    # Test query that should trigger tool
    query = "Tìm thông tin về phương pháp học từ vựng tiếng Anh"

    print(f"Query: {query}")

    initial_state = AgentState(
        query=query,
        last_agent_response="",
        last_agent="",
        tool_observations=[],
        num_steps=0
    )

    print("Initial state:", initial_state)

    try:
        result = agentic_graph.invoke(initial_state)
        print("Final result:")
        print(f"Response: {result['last_agent_response']}")
        print(f"Observations: {result['tool_observations']}")
        print(f"Steps: {result['num_steps']}")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_agent()