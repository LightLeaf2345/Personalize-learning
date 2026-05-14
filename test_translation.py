import os
import django
import sys

# Setup Django
sys.path.append(r'C:\Users\Le The Bao\Desktop\MyProject\nckh\myproject2')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from utils.ai_engine import agentic_graph, AgentState

# Test dịch
state = AgentState(
    query="Dịch 'Hello world' sang tiếng Việt",
    last_agent_response="",
    last_agent="",
    tool_observations=[],
    num_steps=0
)

result = agentic_graph.invoke(state)
print("Last response:", repr(result["last_agent_response"]))
print("Observations:", result["tool_observations"])
print("Steps:", result["num_steps"])
print("Full result:", result)