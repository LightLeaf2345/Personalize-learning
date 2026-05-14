import os
import sys
import json
import pandas as pd
import chromadb
from django.conf import settings
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.utilities import SerpAPIWrapper
from langgraph.graph import StateGraph, END
from typing import TypedDict
from langchain_core.tools import tool
from pydantic import BaseModel, Field

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# --- 1. CẤU HÌNH CHROMADB ---
DB_PATH = os.path.join(settings.BASE_DIR, "chroma_db")
client = chromadb.PersistentClient(path=DB_PATH)
ef = ONNXMiniLM_L6_V2(preferred_providers=['CPUExecutionProvider'])

collection = client.get_or_create_collection(
    name="e_learning_faq",
    embedding_function=ef
)

def tool_get_roadmap(user_id, **kwargs):
    """Kỹ năng: Phân tích lộ trình và HỎI Ý KIẾN người dùng"""
    from learning.models import UserProfile
    import json
    
    try:
        profile, _ = UserProfile.objects.get_or_create(user_id=user_id)
        
        mastery_data = {
            "Ngữ pháp": round(profile.grammar_mastery * 100),
            "Từ vựng": round(profile.vocab_mastery * 100),
            "Nghe": round(profile.listening_mastery * 100)
        }
        weakest_skill = min(mastery_data, key=mastery_data.get)
        lowest_score = mastery_data[weakest_skill]
        
        try:
            weak_topics = json.loads(profile.weak_areas) if isinstance(profile.weak_areas, str) else profile.weak_areas
            weak_topics_str = ", ".join(weak_topics[:3]) if weak_topics else "các chủ đề cơ bản"
        except:
            weak_topics_str = "các chủ đề cơ bản"
            
        context = (
            f"Trình độ hiện tại: Level {profile.level}. "
            f"Điểm số: {mastery_data}. "
            f"Kỹ năng yếu nhất: {weakest_skill} ({lowest_score}/100 điểm). "
            f"Chủ đề đang hổng: {weak_topics_str}. "
            f"LỆNH HỆ THỐNG DÀNH CHO AI: Hãy báo cho người dùng biết điểm yếu, khuyên họ học lý thuyết "
            f"và LỊCH SỰ HỎI XEM họ có muốn bạn chuyển sang trang lý thuyết không. "
            f"BẮT BUỘC ghi thêm cụm '[ASK_THEORY]' vào cuối câu trả lời của bạn."
        )
        return {"context": context, "source": "System_Mastery_Analysis"}
    except Exception as e:
        return {"context": f"Lỗi: {str(e)}", "source": "Django_ORM"}

def init_knowledge_base():
    faq_path = os.path.join(settings.BASE_DIR, "data", "e_learning_faq.csv")
    if os.path.exists(faq_path) and collection.count() == 0:
        df_qa = pd.read_csv(faq_path, sep=';', encoding='utf-8-sig')
        df_qa['combined_text'] = "Question: " + df_qa['Question (Người học hỏi)'].astype(str) + ". Answer: " + df_qa['Answer (Quản gia phản hồi)'].astype(str)
        collection.add(documents=df_qa['combined_text'].tolist(), ids=df_qa.index.astype(str).tolist())
        print("✅ Đã nạp dữ liệu FAQ!")

def tool_get_grammar_exercise(user_id, **kwargs):
    from learning.models import UserProfile, Question
    profile = UserProfile.objects.filter(user_id=user_id).first()
    level = profile.level if profile else 1
    
    q = Question.objects.filter(category="grammar", difficulty=level).order_by('?').first()
    exercise = q.question_text if q else "Không tìm thấy bài tập."
    return {"context": f"Bài tập: {exercise}", "source": "Django_ORM"}

def tool_get_listening_exercise(user_id, **kwargs):
    from learning.models import UserProfile, Question
    profile = UserProfile.objects.filter(user_id=user_id).first()
    level = profile.level if profile else 1
    
    q = Question.objects.filter(category="listening", difficulty=level).order_by('?').first()
    exercise = q.question_text if q else "Không tìm thấy bài nghe."
    return {"context": f"Bài nghe: {exercise}", "source": "Django_ORM"}

def get_learning_support(query=None, **kwargs):
    results = collection.query(query_texts=[query], n_results=1)
    distances = results.get("distances", [[10]])[0]
    
    if not results["documents"] or not results["documents"][0] or distances[0] > 1.2:
        return {
            "context": "Không có thông tin trong tài liệu. Hãy phản hồi tự nhiên theo tư duy của bạn.", 
            "source": "None"
        }
    return {"context": "\n".join(results["documents"][0]), "source": "FAQ"}

def tool_update_level(user_id, direction, **kwargs):
    from learning.models import UserProfile
    profile = UserProfile.objects.filter(user_id=user_id).first()
    if not profile:
        return {"context": "Lỗi: Không tìm thấy người dùng.", "source": "System"}
        
    current_level = profile.level
    new_level = current_level + 1 if direction == "up" else current_level - 1
    
    if 1 <= new_level <= 3:
        profile.level = new_level
        profile.save()
        return {"context": f"Đã cập nhật trình độ lên Level {new_level}.", "source": "System_Adaptive"}
    return {"context": "Giữ nguyên level (đã đạt mốc tối đa/tối thiểu).", "source": "System_Adaptive"}

def tool_search_related_courses(topic: str, user_id: str = None, **kwargs):
    emap_path = os.path.join(settings.BASE_DIR, "data", "e_map.csv")
    if not os.path.exists(emap_path):
        return {"context": "Dữ liệu khóa học (e_map.csv) không tồn tại.", "source": "E-learning Map"}
    
    user_level = 1
    if user_id:
        from learning.models import UserProfile
        profile = UserProfile.objects.filter(user_id=user_id).first()
        user_level = profile.level if profile else 1

    try:
        df_br = pd.read_csv(emap_path, sep=';')
        mask = (df_br['course_name'].str.contains(topic, case=False, na=False)) | \
               (df_br['description'].str.contains(topic, case=False, na=False))
        mask &= (df_br['level'].astype(int) <= int(user_level))
        
        results_df = df_br[mask]
        if not results_df.empty:
            context = results_df[['course_name', 'duration', 'rating']].head(3).to_dict(orient='records')
            return {"context": f"Các khóa học gợi ý cho trình độ Level {user_level}: {context}", "source": "E-learning Map"}
        else:
            return {"context": f"Không tìm thấy khóa học nào phù hợp với chủ đề '{topic}' ở trình độ Level {user_level}.", "source": "E-learning Map"}
    except Exception as e:
        return {"context": f"Lỗi khi đọc file khóa học: {str(e)}", "source": "E-learning Map"}

def web_search(query, **kwargs):
    search = SerpAPIWrapper()
    return {"context": search.run(query), "source": "Google Search"}
    
TOOLS_MAPPING = {
    "get_roadmap": tool_get_roadmap,
    "get_grammar": tool_get_grammar_exercise,
    "get_listening": tool_get_listening_exercise,
    "get_faq": get_learning_support,
    "web_search": web_search,
    "update_level": tool_update_level,
    "search_related_courses": tool_search_related_courses
}

# =========================================================
# KHAI BÁO TOOL LLM CHO LANGCHAIN (NÂNG CẤP NATIVE CALLING)
# =========================================================
class RoadmapSchema(BaseModel):
    action_intent: str = Field(description="Ghi 'check_roadmap' để xác nhận hành động này")

@tool("get_roadmap", args_schema=RoadmapSchema)
def get_roadmap(action_intent: str):
    """Gọi công cụ này BẮT BUỘC khi người học hỏi về 'Tôi nên học gì?', 'Lộ trình học', 'Tình hình học tập', 'Điểm yếu của tôi'."""
    pass

class UpdateLevelSchema(BaseModel):
    direction: str = Field(description="Nhập 'up' để tăng độ khó, 'down' để giảm độ khó")

@tool("update_level", args_schema=UpdateLevelSchema)
def update_level(direction: str):
    """BẮT BUỘC gọi khi người học than bài quá dễ (direction='up') hoặc quá khó/không hiểu (direction='down')."""
    pass

class SearchCoursesSchema(BaseModel):
    topic: str = Field(description="Chủ đề khóa học cần tìm, ví dụ: 'Ngữ pháp', 'Từ vựng'")

@tool("search_related_courses", args_schema=SearchCoursesSchema)
def search_related_courses(topic: str):
    """Gọi công cụ này để tìm kiếm các khóa học liên quan dựa trên chủ đề người dùng quan tâm."""
    pass

llm_tools = [get_roadmap, update_level, search_related_courses]

# --- 2. CẤU HÌNH BỘ NÃO (LANGGRAPH) ---
class AgentState(TypedDict):
    user_id: str
    query: str
    last_agent_response: str
    tool_observations: list
    num_steps: int

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=settings.GEMINI_API_KEY, temperature=0.4)
llm_with_tools = llm.bind_tools(llm_tools) 

SYSTEM_PROMPTS = {
    "agent_main": """Bạn là Quản gia AI tại LEARNAPP - Một trí tuệ nhân tạo lịch thiệp, thấu hiểu và là Cố vấn học tập cá nhân của người dùng.

    QUY TẮC XỬ LÝ TÌNH HUỐNG (Tuyệt đối tuân thủ):
    1. TÂM SỰ, DỊCH THUẬT & TRÒ CHUYỆN: Nếu người học than mệt, chào hỏi, hoặc yêu cầu DỊCH THUẬT -> Hãy trả lời tự nhiên, giải đáp ngay lập tức.
    2. HỎI BÀI TẬP: Nếu họ hỏi "Tại sao sai câu này?", "Giải thích giúp tôi" -> Hãy lấy thông tin từ 'Observations' để giải thích trọng tâm.
    3. TƯ VẤN LỘ TRÌNH (HỎI Ý KIẾN): 
       - Khi người học hỏi "Nên học gì tiếp?", "Lộ trình học" -> BẮT BUỘC dùng Tool 'get_roadmap'.
       - Khi Observations trả về kết quả lộ trình, hãy khuyên họ ôn lý thuyết và LỊCH SỰ HỎI XIN PHÉP (VD: "Quản gia đưa bạn sang trang lý thuyết ôn lại nhé?").
       - BẮT BUỘC đính kèm chữ [ASK_THEORY] vào cuối câu trả lời.
    4. THỰC THI ĐIỀU HƯỚNG: 
       - Nếu người học đồng ý chuyển trang -> BẮT BUỘC thêm cụm từ này vào CUỐI câu trả lời: COMMAND_ACTION:NAVIGATE:theory
    5. ĐIỀU CHỈNH ĐỘ KHÓ: 
       - Khi than bài quá dễ/khó -> BẮT BUỘC dùng Tool 'update_level'.

    QUY TẮC TRÌNH BÀY (BẮT BUỘC ĐỂ DỄ ĐỌC):
    - KHÔNG viết thành một đoạn văn dài lê thê. Phải tách đoạn và có khoảng trắng.
    - Trình bày dạng Bullet point (-) hoặc đánh số (1, 2) rõ ràng.
    - Dùng in đậm (**chữ**) cho các từ khóa, đáp án.
    - Khi giải thích bài tập, hãy chia làm 3 ý rõ ràng: 
      👉 **Đáp án đúng:** [Chỉ ra đáp án]
      👉 **Lý do:** [Giải thích ngắn gọn]
      👉 **Cấu trúc cần nhớ:** [Rút ra quy tắc]
    - Khi tư vấn lộ trình, tách rõ 2 ý: **📊 Tình trạng hiện tại:** và **💡 Gợi ý của Quản gia:**

    PHONG CÁCH GIAO TIẾP:
    - Danh xưng: "Quản gia" - "Bạn".
    - Giọng điệu: Thông minh, tinh tế. Thêm emoji cho sinh động, nhưng không lạm dụng.""",

    "agent_course_expert": """Bạn là Chuyên gia Tư vấn Lộ trình của LEARNAPP.
    Nhiệm vụ: Dựa vào trình độ hiện tại của người học và dữ liệu từ Observations, hãy chọn lọc và phân tích xem khóa học nào thực sự cần thiết cho họ.
    Quy tắc: Không liệt kê máy móc. Hãy giải thích rõ "Tại sao khóa học này lại giúp bạn bứt phá ở Level hiện tại"."""
}

def call_agent(state: AgentState, agent_name: str):
    prompt = f"{SYSTEM_PROMPTS[agent_name]}\nQuery: {state['query']}\nObservations: {state['tool_observations']}"
    response = llm_with_tools.invoke(prompt)
    
    if response.tool_calls:
        state["last_agent_response"] = json.dumps({"tool_calls": response.tool_calls})
    else:
        content = response.content
        if isinstance(content, list):
            text_parts = [item.get("text", "") if isinstance(item, dict) else str(item) for item in content]
            state["last_agent_response"] = " ".join(text_parts)
        else:
            state["last_agent_response"] = str(content) if content else ""
        
    state["last_agent"] = agent_name
    state["num_steps"] += 1
    return state

def call_tool(state: AgentState):
    res = state["last_agent_response"]
    try:
        parsed = json.loads(res)
        tool_calls = parsed.get("tool_calls", [])
        
        for tc in tool_calls:
            tool_name = tc["name"]
            kwargs = tc["args"]
            kwargs["user_id"] = state["user_id"]
            
            if tool_name in TOOLS_MAPPING:
                print(f"🛠️ [Native Calling] Thực thi Tool: {tool_name} với tham số: {kwargs}")
                result = TOOLS_MAPPING[tool_name](**kwargs)
                observation = result.get('context', str(result))
                state["tool_observations"].append(f"[{tool_name} kết quả]: {observation}")
            else:
                state["tool_observations"].append(f"Lỗi: Không hỗ trợ tool {tool_name}")
                
    except Exception as e:
        print(f"❌ Lỗi thực thi Tool: {e}")
        state["tool_observations"].append(f"Lỗi khi gọi Tool: {str(e)}")
        
    return state

# --- 5. XÂY DỰNG LUỒNG (GRAPH) ---

workflow = StateGraph(AgentState)
workflow.add_node("agent_main", lambda x: call_agent(x, "agent_main"))
workflow.add_node("agent_course_expert", lambda x: call_agent(x, "agent_course_expert"))
workflow.add_node("tools", call_tool)

workflow.set_entry_point("agent_main")

def should_continue(state):
    if state["num_steps"] > 2: return END
    res = state["last_agent_response"]
    
    try:
        parsed = json.loads(res)
        if "tool_calls" in parsed: 
            return "continue"
    except:
        pass
        
    if "HANDOFF:agent_course_expert" in res: return "handoff_expert"
    return END

workflow.add_conditional_edges("agent_main", should_continue, {"continue": "tools", "handoff_expert": "agent_course_expert", END: END})
workflow.add_conditional_edges("agent_course_expert", should_continue, {"continue": "tools", END: END})
workflow.add_edge("tools", "agent_main")

agentic_graph = workflow.compile()

try:
    init_knowledge_base()
except Exception as e:
    print(f"⚠️ Chưa nạp được dữ liệu FAQ: {e}")