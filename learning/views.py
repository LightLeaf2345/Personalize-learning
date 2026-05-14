# learning/views.py
import random
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.auth import login
import json

# === SỬ DỤNG TRỰC TIẾP MODEL CỦA DJANGO (KHÔNG DÙNG DATABASEMANAGER NỮA) ===
from .models import Attempt, UserProfile, Question, Lesson 
from .forms import SignupForm
from utils.ai_engine import AgentState, agentic_graph, get_learning_support

# ============================================
# CÁC TRANG GIAO DIỆN
# ============================================

def home(request):
    return render(request, "learning/index.html", {})

def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("learning:home")
    else:
        form = SignupForm()

    return render(request, "registration/signup.html", {"form": form})


# ============================================
# API XỬ LÝ DỮ LIỆU BẰNG DJANGO ORM
# ============================================

@login_required
def get_question(request):
    category = request.GET.get("category", "grammar")
    
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    current_level = profile.level 
    
    # --- LOGIC CÁ NHÂN HÓA: ƯU TIÊN VÙNG YẾU ---
    target_sub_category = None
    if profile.weak_areas and random.random() < 0.7:
        target_sub_category = random.choice(profile.weak_areas)
    
    answered_ids = request.session.get(f'answered_{category}_ids', [])
    
    # BƯỚC 1: Tìm câu hỏi khớp với Level hiện tại và chưa làm
    questions_query = Question.objects.filter(category=category, difficulty=current_level).exclude(id__in=answered_ids)
    
    if category == "grammar" and target_sub_category:
        weak_questions = questions_query.filter(sub_category=target_sub_category)
        if weak_questions.exists():
            questions_query = weak_questions
            
    q_obj = questions_query.order_by('?').first()
    
    # BƯỚC 2: LƯỚI AN TOÀN 1 - Nếu đã làm hết câu hỏi ở level này -> Xóa lịch sử và lấy lại từ đầu
    if not q_obj:
        answered_ids = []
        request.session[f'answered_{category}_ids'] = answered_ids
        q_obj = Question.objects.filter(category=category, difficulty=current_level).order_by('?').first()

    # BƯỚC 3: LƯỚI AN TOÀN 2 (QUAN TRỌNG) - Nếu database hoàn toàn KHÔNG CÓ câu hỏi nào cho Level này 
    # (Ví dụ: Bài nghe chỉ có level 2, nhưng học viên đang level 1) -> Tự động lấy bài ở level khác
    if not q_obj:
        q_obj = Question.objects.filter(category=category).order_by('?').first()

    # BƯỚC 4: Lưới an toàn cuối cùng, nếu database thật sự trống rỗng
    if not q_obj:
        return JsonResponse({"error": "No question available"}, status=404)

    # Lưu lại lịch sử đã làm
    answered_ids.append(q_obj.id)
    request.session[f'answered_{category}_ids'] = answered_ids

    # Gói dữ liệu gửi về Web (Đã bao gồm đường dẫn media_url cho Audio)
    payload = {
        "id": q_obj.id, 
        "question_text": q_obj.question_text,
        "options": q_obj.options,
        "correct_answer": q_obj.correct_answer, 
        "explanation": q_obj.explanation, 
        "difficulty": current_level,
        "category": category,
        "sub_category": q_obj.sub_category,
        "media_url": q_obj.media_url
    }
    
    request.session['current_sql_question'] = payload
    return JsonResponse({"success": True, "question": payload})

@require_POST
@login_required
def check_answer(request):
    try:
        data = json.loads(request.body)
        answer = data.get("answer", "").strip()
    except Exception:
        return HttpResponseBadRequest("Invalid payload")

    current_q = request.session.get('current_sql_question')
    if not current_q:
        return HttpResponseBadRequest("No active question to answer")

    from .rl_agent import ReinforcementLearningAgent
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    agent = ReinforcementLearningAgent(profile)
    
    state_before = agent._state_key()

    is_correct = (answer.lower().strip() == current_q['correct_answer'].lower().strip())
    category = current_q.get("category", "grammar") 
    sub_cat = current_q.get("sub_category", "general")

    old_level = profile.level

    reward = agent.calculate_reward(is_correct, sub_cat)
    
    xp_gained = 0
    xp_lost = 0

    if is_correct:
        xp_gained = int(reward) if int(reward) > 0 else 15
        profile.add_xp(xp_gained) 
    else:
        xp_lost = abs(int(reward)) if int(reward) < 0 else 5
        profile.xp = max(0, profile.xp - xp_lost) 
        profile.save()

    is_level_up = profile.level > old_level

    agent.update_mastery(category, sub_cat, is_correct)
    
    state_after = agent._state_key()
    agent.update_q_value(state_before, "Recommend_Exercise", reward, state_after)

    profile.last_active = timezone.now()
    profile.save()

    current_mastery = getattr(profile, f"{category.lower()}_mastery", profile.grammar_mastery)

    return JsonResponse({
        "success": True,
        "correct": is_correct,
        "correct_answer": current_q['correct_answer'],
        "xp_gained": xp_gained, 
        "xp_lost": xp_lost,     
        "level_up": is_level_up, 
        "current_level": profile.level,
        "new_mastery": current_mastery,
        "explanation": current_q['explanation']
    })

# ============================================
# API HỖ TRỢ BẰNG AI VÀ GIÁO TRÌNH
# ============================================

@require_POST
@csrf_exempt
def get_ai_help(request):
    try:
        data = json.loads(request.body)
        user_query = data.get("query", "").strip()
        user_query_lower = user_query.lower()

        if any(word in user_query_lower for word in ["tăng độ khó", "khó hơn", "nâng level"]):
            request.user.learning_profile.add_xp(110)
            return JsonResponse({"success": True, "command": "REFRESH_LEVEL", "direction": "up", "response": ""})

        if any(word in user_query_lower for word in ["dễ quá", "giảm độ khó", "dễ hơn"]):
            request.user.learning_profile.add_xp(-110)
            return JsonResponse({"success": True, "command": "REFRESH_LEVEL", "direction": "down", "response": ""})

        if request.session.get('ai_asked_theory'):
            if any(word in user_query_lower for word in ["ok", "có", "đồng ý", "vâng", "chuyển", "được", "đi", "ừ"]):
                request.session['ai_asked_theory'] = False
                return JsonResponse({
                    "success": True,
                    "response": "Tuân lệnh! Quản gia đang lấy xe đưa bạn sang thư viện lý thuyết đây.",
                    "command": "GO_TO_THEORY" 
                })
            elif any(word in user_query_lower for word in ["không", "thôi", "từ chối", "khoan", "chưa"]):
                request.session['ai_asked_theory'] = False
                return JsonResponse({
                    "success": True,
                    "response": "Quản gia đã rõ. Chúng ta sẽ ở lại đây luyện tập tiếp nhé!",
                    "command": None
                })
            request.session['ai_asked_theory'] = False 

        roadmap_keywords = ["nên học gì", "lộ trình", "điểm yếu", "tình hình học", "học cái gì", "trình độ hiện tại"]
        if any(word in user_query_lower for word in roadmap_keywords):
            try:
                profile = request.user.learning_profile
                m_data = {
                    "Ngữ pháp": round(profile.grammar_mastery * 100),
                    "Từ vựng": round(profile.vocab_mastery * 100),
                    "Nghe": round(profile.listening_mastery * 100)
                }
                weakest_skill = min(m_data, key=m_data.get)
                lowest_score = m_data[weakest_skill]
                
                try:
                    weak_list = json.loads(profile.weak_areas) if isinstance(profile.weak_areas, str) else profile.weak_areas
                    weak_str = ", ".join(weak_list[:3]) if weak_list else "các chủ đề cơ bản"
                except:
                    weak_str = "các chủ đề cơ bản"

                request.session['ai_asked_theory'] = True
                
                local_response = (
                    f"Quản gia vừa kiểm tra sổ tay học tập của bạn, kết quả đây nhé:\n\n"
                    f"**📊 Tình trạng hiện tại:**\n"
                    f"- Kỹ năng **{weakest_skill}** đang báo động đỏ (chỉ đạt **{lowest_score}/100 điểm**).\n"
                    f"- Đặc biệt bạn đang hổng kiến thức ở phần: **{weak_str}**.\n\n"
                    f"**💡 Gợi ý của Quản gia:**\n"
                    f"Để không mất gốc, Quản gia xin phép đưa bạn sang thư viện lý thuyết để ôn tập lại ngay nhé, bạn có đồng ý không?"
                )
                
                return JsonResponse({
                    "success": True,
                    "response": local_response,
                    "command": None 
                })
            except Exception as e:
                pass 

        if user_query_lower in ["chào", "hi", "hello", "xin chào"]:
            return JsonResponse({
                "success": True,
                "response": f"Xin chào {request.user.username}! Quản gia đây, bạn cần giúp gì không?",
                "command": None
            })

        current_q = request.session.get('current_sql_question')
        question_context = ""
        if current_q:
            question_context = f"\nBối cảnh câu hỏi: {current_q['question_text']}\nCác lựa chọn: {', '.join(current_q['options'])}"

        try:
            state = AgentState(
                user_id=str(request.user.id),
                query=f"[User: {request.user.username}] {user_query} {question_context}",
                last_agent_response="",
                tool_observations=[], 
                num_steps=0
            )
            
            result = agentic_graph.invoke(state)
            final_response = result.get("last_agent_response", "Quản gia đang suy nghĩ...")
            
            is_navigating = False
            
            if "COMMAND_ACTION:NAVIGATE:theory" in final_response:
                is_navigating = True
                final_response = final_response.replace("COMMAND_ACTION:NAVIGATE:theory", "").strip()
                
            if "[ASK_THEORY]" in final_response:
                request.session['ai_asked_theory'] = True
                final_response = final_response.replace("[ASK_THEORY]", "").strip()
            else:
                request.session['ai_asked_theory'] = False
            
            return JsonResponse({
                "success": True,
                "response": final_response,
                "command": "GO_TO_THEORY" if is_navigating else None
            })

        except Exception as ai_err:
            print(f"🔥🔥🔥 LỖI AI CHÍNH XÁC LÀ: {repr(ai_err)}")
            explanation = "Rất tiếc, Quản gia đang mất kết nối với bộ não AI."
            if current_q and current_q.get('explanation'):
                explanation = current_q['explanation']
            
            return JsonResponse({
                "success": True,
                "response": f"⚠️ [Chế độ ngoại tuyến]: {explanation}",
                "command": None
            })

    except Exception as e:
        return JsonResponse({"error": f"Lỗi hệ thống: {str(e)}"}, status=500)

@require_POST
@login_required
def get_explanation(request):
    try:
        current_q = request.session.get('current_sql_question')
        if not current_q:
            return JsonResponse({"error": "No active question found"}, status=400)
        
        explanation_query = f"Giải thích chi tiết câu hỏi sau:\n{current_q['question_text']}\n\nĐáp án đúng: {current_q['correct_answer']}"
        result = get_learning_support(query=explanation_query)
        
        return JsonResponse({
            "success": True,
            "explanation": current_q['explanation'] or result.get("context", "Không có giải thích"),
            "ai_insight": result.get("context", "")
        })
    except Exception as e:
        return JsonResponse({"error": f"Error: {str(e)}"}, status=500)

@login_required    
def curriculum_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    current_level = profile.level 
    
    # Lấy danh sách giáo trình thẳng từ Database của Django
    lessons_qs = Lesson.objects.all().order_by('level', 'order_num')
    lessons = []
    for l in lessons_qs:
        lessons.append({
            "id": l.id,
            "title": l.title,
            "level": l.level,
            "is_locked": l.level > current_level # Khóa nếu level bài học cao hơn level user
        })
        
    return render(request, "learning/curriculum.html", {"lessons": lessons})

@login_required
def get_lesson_api(request, lesson_id):
    # Lấy chi tiết bài học từ Database Django
    lesson = Lesson.objects.filter(id=lesson_id).first()
    if lesson:
        return JsonResponse({
            "success": True, 
            "lesson": {
                "title": lesson.title, 
                "content": lesson.content_html
            }
        })
    return JsonResponse({"success": False, "error": "Not found"})