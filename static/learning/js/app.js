// learning/static/learning/js/app.js
document.addEventListener("DOMContentLoaded", function() {
  // --- CURRICULUM LOGIC ---
  const lessonItems = document.querySelectorAll(".lesson-item");
  const lessonTitle = document.getElementById("active-lesson-title");
  const lessonBody = document.getElementById("active-lesson-body");
  const placeholder = document.getElementById("curriculum-placeholder");
  const lessonDisplay = document.getElementById("curriculum-display");

  window.loadLesson = async function(id, element) {
    // === CHẶN CLICK NẾU BÀI HỌC BỊ KHÓA ===
    if (element.getAttribute('data-locked') === 'true') {
        alert("🔒 BÀI HỌC BỊ KHÓA!\n\nBạn chưa đủ cấp độ để mở bài học này. Hãy vào mục 'Luyện tập' kiếm thêm XP để thăng cấp nhé!");
        return; // Dừng lại ngay lập tức, không gọi API lấy nội dung nữa
    }
    // ======================================

    console.log("Đang gọi bài học ID:", id); 

    // 1. Highlight bài học đang chọn (Sidebar)
    document.querySelectorAll('.lesson-item').forEach(el => el.classList.remove('active'));
    element.classList.add('active');

    // 2. Gọi API lấy nội dung
    try {
        const res = await fetch(`/api/lesson/${id}/`); 
        const data = await res.json();

        if (data.success) {
            const placeholder = document.getElementById('curriculum-placeholder');
            const displayArea = document.getElementById('curriculum-display');
            const bodyArea = document.getElementById('active-lesson-body');
            
            if (placeholder) placeholder.style.display = 'none';
            if (displayArea) {
                displayArea.style.display = 'block';
                // Reset lại animation bằng cách xóa và thêm lại class
                bodyArea.classList.remove('lesson-pro');
                void bodyArea.offsetWidth; // "Trình duyệt ơi, hãy tính toán lại đi"
                bodyArea.classList.add('lesson-pro');
            }

            document.getElementById('active-lesson-title').textContent = data.lesson.title;
            bodyArea.innerHTML = data.lesson.content;

            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    } catch (err) {
        console.error("Lỗi kết nối API:", err);
    }
  };

  const loadBtn = document.getElementById("load-question-btn");
  const qbox = document.getElementById("question-box");
  const qtext = document.getElementById("q-text");
  const qlevel = document.getElementById("q-level");
  const optionsDiv = document.getElementById("options");
  const submitBtn = document.getElementById("submit-answer-btn");
  const nextBtn = document.getElementById("next-question-btn");
  const feedbackDiv = document.getElementById("feedback");
  
  // AI Elements
  const aiChat = document.getElementById("ai-chat");
  const aiInput = document.getElementById("ai-input");
  const getExplanationBtn = document.getElementById("get-explanation-btn");
  const getHintBtn = document.getElementById("get-hint-btn");
  const askAiBtn = document.getElementById("ask-ai-btn");
  
  let currentQuestion = null;
  let selected = null;
  
  // BIẾN LƯU TRẠNG THÁI CHẾ ĐỘ HỌC (Mặc định là Ngữ pháp)
  let currentMode = 'grammar'; 

  // HÀM CHUYỂN ĐỔI CHẾ ĐỘ HỌC
  window.switchMode = function(mode) {
      currentMode = mode;
      
      // 1. Đổi màu nút bấm để báo hiệu đang chọn cái nào
      document.getElementById('mode-grammar').classList.remove('active');
      document.getElementById('mode-listening').classList.remove('active');
      document.getElementById(`mode-${mode}`).classList.add('active');
      
      // 2. Tự động tải câu hỏi mới thuộc chế độ vừa chọn
      loadQuestion(); 
  };

  function getCsrfToken() {
    const cookies = document.cookie.split(";").map(c => c.trim());
    for (let c of cookies) {
      if (c.startsWith("csrftoken=")) return c.split("=")[1];
    }
    return "";
  }

  // BỔ SUNG: Hàm dịch Markdown sang HTML
  function formatAiText(text) {
      if (!text) return "";
      return text
          .replace(/\*\*(.*?)\*\*/g, '<strong style="color: #0056b3;">$1</strong>') // In đậm chữ xanh
          .replace(/\*(.*?)\*/g, '<em>$1</em>') // In nghiêng
          .replace(/\n/g, '<br>'); // Xuống dòng
  }

  // NÂNG CẤP: Hàm addAiMessage có hiệu ứng gõ chữ
  function addAiMessage(text, isUser = false) {
      const msgDiv = document.createElement("div");
      msgDiv.className = `ai-message ${isUser ? "user" : "assistant"}`;
      aiChat.appendChild(msgDiv);

      if (isUser) {
          // Tin nhắn của người dùng thì hiện luôn ngay lập tức
          msgDiv.textContent = text;
          aiChat.scrollTop = aiChat.scrollHeight;
      } else {
          // Tin nhắn của AI thì áp dụng hiệu ứng Typewriter (Gõ chữ)
          const htmlString = formatAiText(text);
          let i = 0;
          let isTag = false;
          let currentHtml = "";

          function type() {
              if (i < htmlString.length) {
                  currentHtml += htmlString.charAt(i);
                  msgDiv.innerHTML = currentHtml;
                  
                  // Nhận diện thẻ HTML để không bị gõ từng ký tự của thẻ <br> hay <strong>
                  if (htmlString.charAt(i) === "<") isTag = true;
                  if (htmlString.charAt(i) === ">") isTag = false;
                  
                  i++;
                  aiChat.scrollTop = aiChat.scrollHeight; // Tự động cuộn xuống
                  setTimeout(type, isTag ? 0 : 15); // Tốc độ gõ: 15 mili-giây / 1 chữ
              }
          }
          type();
      }
  } 

  async function callAiApi(query, questionId = null) {
    addAiMessage(query, true); // Tin nhắn của User
    addAiMessage("🤔 Đang suy nghĩ...", false); // Tin nhắn chờ của AI
    
    try {
      const res = await fetch("/api/get_ai_help/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken()
        },
        body: JSON.stringify({
          query: query,
          question_id: questionId
        })
      });
      
      const data = await res.json();
      
      // Xóa tin nhắn "🤔 Đang suy nghĩ..."
      const messages = aiChat.querySelectorAll(".ai-message");
      if (messages.length > 0) {
        messages[messages.length - 1].remove();
      }
      
      if (data.success) {
        // TRƯỜNG HỢP 1: Đổi độ khó
        if (data.command === "REFRESH_LEVEL") {
            loadQuestion(); // Xóa sạch chat cũ và nạp câu hỏi mới
            
            // Đợi câu hỏi mới render xong rồi AI mới nhắn tin
            setTimeout(() => {
                const statusMsg = data.direction === "up" 
                    ? "🚀 Quản gia đã nâng cấp thử thách! Chúc bạn chinh phục mức độ mới." 
                    : "✅ Đã hạ độ khó. Chúng ta cùng ôn lại căn bản nhé.";
                addAiMessage(statusMsg, false);
            }, 800); 
            return; 
        }

        // TRƯỜNG HỢP 2: Đi đến giáo trình
        if (data.command === "GO_TO_THEORY") {
            // Hiện lý do AI bắt đi học 
            const theoryMsg = data.response && data.response.trim() !== "" 
                ? data.response 
                : "🚀 Điểm số đang báo động. Quản gia đưa bạn sang trang lý thuyết nhé...";
                
            addAiMessage(theoryMsg, false);
            
            // Đợi 2.5 giây (2500ms) để người học đọc "lời phán quyết" rồi mới chuyển trang
            setTimeout(() => { window.location.href = "/curriculum/"; }, 2500);
            return; 
        }

        // TRƯỜNG HỢP 3: Chat bình thường
        if (data.response && data.response.trim() !== "") {
            addAiMessage(data.response, false);
        }

      } else {
        addAiMessage("❌ Lỗi: " + (data.error || "Không thể lấy trợ giúp"), false);
      }

    } catch (err) {
      console.error("LỖI THỰC SỰ LÀ:", err);
      // Xóa tin nhắn "Đang suy nghĩ..."
      const messages = aiChat.querySelectorAll(".ai-message");
      if (messages.length > 0 && messages[messages.length - 1].textContent.includes("suy nghĩ")) {
        messages[messages.length - 1].remove();
      }
      
      // In thẳng cái lỗi thực sự ra màn hình để bắt bệnh!
      addAiMessage(`❌ Lỗi hệ thống: ${err.name} - ${err.message}`, false);
    }
  }

  async function getExplanation() {
    if (!currentQuestion) {
      addAiMessage("⚠️ Vui lòng tải một câu hỏi trước", false);
      return;
    }
    callAiApi(`Giải thích chi tiết câu hỏi: "${currentQuestion.question_text}" với đáp án đúng`, currentQuestion.id);
  }

  async function getHint() {
    if (!currentQuestion) {
      addAiMessage("⚠️ Vui lòng tải một câu hỏi trước", false);
      return;
    }
    callAiApi(`Cho tôi một gợi ý để trả lời câu hỏi này: "${currentQuestion.question_text}"`, currentQuestion.id);
  }

  function clearAiChat() {
    aiChat.innerHTML = "";
  }

  // ==========================================
  // LOAD QUESTION 
  // ==========================================
  async function loadQuestion() {
    feedbackDiv.innerHTML = "";
    selected = null;
    clearAiChat();
    addAiMessage("👋 Xin chào! Tôi sẵn sàng giúp bạn.", false);
    
    try {
      const res = await fetch(`/api/get_question/?category=${currentMode}`);
      const data = await res.json();

      if (data.success) {
        currentQuestion = data.question;
        qbox.style.display = "block";
        
        // --- XỬ LÝ ÂM THANH (AUDIO) ---
        const oldAudio = document.getElementById("q-audio-player");
        if (oldAudio) oldAudio.remove();

        if (currentQuestion.media_url) {
            const audioDiv = document.createElement("div");
            audioDiv.id = "q-audio-player";
            audioDiv.style.marginBottom = "20px";
            audioDiv.style.textAlign = "center";
            
            audioDiv.innerHTML = `
                <audio controls style="width: 100%; outline: none; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1);">
                    <source src="${currentQuestion.media_url}" type="audio/mpeg">
                    Trình duyệt của bạn không hỗ trợ thẻ audio.
                </audio>
            `;
            qtext.parentNode.insertBefore(audioDiv, qtext);
        }
        // -------------------------------

        qtext.textContent = currentQuestion.question_text || currentQuestion.sentence || "Vui lòng nghe đoạn băng và chọn đáp án.";
        
        // --- ĐOẠN CẬP NHẬT ĐỘ KHÓ THÔNG MINH ---
        const levelName = currentQuestion.difficulty === 1 ? "Beginner" : 
                          currentQuestion.difficulty === 2 ? "Intermediate" : "Advanced";
        
        // 1. Cập nhật nhãn ngay tại câu hỏi
        qlevel.textContent = `(${levelName})`;
        
        // 2. Cập nhật nhãn trên thanh điều hướng
        const navBadge = document.getElementById('nav-user-level');
        if (navBadge) {
            navBadge.textContent = levelName;
            navBadge.style.color = levelName === "Beginner" ? "#16a34a" : (levelName === "Intermediate" ? "#ca8a04" : "#dc2626");
        }
        // ---------------------------------------

        optionsDiv.innerHTML = "";
        currentQuestion.options.forEach(opt => {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "opt";
          btn.textContent = opt;
          btn.onclick = () => {
            document.querySelectorAll(".opt").forEach(x => x.classList.remove("sel"));
            btn.classList.add("sel");
            selected = opt;
          };
          optionsDiv.appendChild(btn);
        });
        
        submitBtn.style.display = "inline-block";
        nextBtn.style.display = "none";
      } else {
        alert("Hiện chưa có câu hỏi trong kho dữ liệu phần này.");
      }
    } catch (err) {
      console.error(err);
      alert("Lỗi kết nối! Không thể tải câu hỏi.");
    }
  }

  // ==========================================
  // SUBMIT ANSWER 
  // ==========================================
  async function submitAnswer() {
    const feedbackDiv = document.getElementById("feedback");
    
    if (!currentQuestion) {
      feedbackDiv.innerHTML = `<div style="background: #fff3cd; color: #856404; padding: 12px; border-radius: 8px; margin-top: 15px;">⚠️ Vui lòng ấn "Bắt đầu ngay" để tải câu hỏi.</div>`;
      return;
    }
    
    if (!selected) {
      feedbackDiv.innerHTML = `<div style="background: #fff3cd; color: #856404; padding: 12px; border-radius: 8px; margin-top: 15px;">⚠️ Bạn chưa chọn đáp án nào! Vui lòng chọn một phương án trước khi nộp bài.</div>`;
      return;
    }

    feedbackDiv.innerHTML = "";

    try {
      const res = await fetch("/api/check_answer/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken()
        },
        body: JSON.stringify({
          question_id: currentQuestion.id,
          answer: selected
        })
      });
      const result = await res.json();
      
      const allOptionBtns = document.querySelectorAll(".opt");

      allOptionBtns.forEach(btn => {
        btn.disabled = true;
        btn.style.cursor = "default";

        if (btn.textContent === result.correct_answer) {
          btn.classList.add("correct-highlight");
        } 
        
        if (btn.textContent === selected && !result.correct) {
          btn.classList.add("incorrect-highlight");
        }
      });

      // =========================================================
      // GIAO DIỆN CỘNG/TRỪ ĐIỂM
      // =========================================================
      if (result.correct) {
        let successMsg = `✨ Tuyệt vời! Bạn đã trả lời đúng và nhận được <strong style="color: #16a34a;">+${result.xp_gained} XP</strong>.`;
        
        if (result.level_up) {
            let newLevelName = result.current_level === 2 ? 'Intermediate' : 'Advanced';
            successMsg += `<br><br>🎉 <strong>CHÚC MỪNG!</strong> Bạn đã thăng cấp lên <strong>Level ${newLevelName}</strong>!`;
            
            const badge = document.getElementById('nav-user-level');
            if(badge) {
                badge.textContent = newLevelName;
                badge.style.transition = "all 0.5s ease";
                badge.style.color = "#16a34a"; 
                badge.style.transform = "scale(1.2)";
                setTimeout(() => {
                    badge.style.transform = "scale(1)";
                    badge.style.color = ""; 
                }, 1000);
            }
        }

        feedbackDiv.innerHTML = `<div class="correct" style="margin-top: 15px; padding: 15px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px;">
            ${successMsg} 
            <div class="explain" style="margin-top: 10px; font-weight: normal; color: #15803d;"><strong>Giải thích:</strong> ${result.explanation || ""}</div>
        </div>`;

      } else {
        // --- GIAO DIỆN MÀU ĐỎ KHI BỊ TRỪ ĐIỂM ---
        let failMsg = `💡 Tiếc quá! Bạn đã chọn sai và bị trừ <strong style="color: #dc2626;">-${result.xp_lost} XP</strong>.`;
        
        feedbackDiv.innerHTML = `<div class="incorrect" style="margin-top: 15px; padding: 15px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 10px; color: #991b1b;">
            ${failMsg} 
            <div class="explain" style="margin-top: 10px; font-weight: normal; color: #7f1d1d;"><strong>Giải thích:</strong> ${result.explanation || "Không có giải thích cho câu hỏi này."}</div>
        </div>`;
      }
      // =========================================================
      
      document.getElementById("submit-answer-btn").style.display = "none";
      document.getElementById("next-question-btn").style.display = "inline-block";
    } catch (err) {
      console.error(err);
      feedbackDiv.innerHTML = `<div class="incorrect">❌ Lỗi kết nối mạng, vui lòng thử lại.</div>`;
    }
  }

  // Event Listeners
  const practiceCard = document.getElementById("practice-card"); // Nhận diện cả khối card

  // Hàm dùng chung để ẩn menu và bắt đầu bài tập
  const startPractice = () => {
      const welcomeBox = document.querySelector('.learning-options');
      if(welcomeBox) welcomeBox.style.display = 'none';
      const welcomeHeader = document.querySelector('.welcome-header');
      if(welcomeHeader) welcomeHeader.style.display = 'none';
      
      loadQuestion();
  };

  // 1. Cho phép bấm vào Nút "Bắt đầu ngay"
  if (loadBtn) {
      loadBtn.addEventListener("click", startPractice);
  }

  // 2. Cho phép bấm vào CẢ KHỐI Card
  if (practiceCard) {
      practiceCard.addEventListener("click", function(e) {
          // Chỉ kích hoạt nếu người dùng không bấm thẳng vào cái nút (để tránh bị chạy 2 lần)
          if (e.target.id !== 'load-question-btn') {
              startPractice();
          }
      });
  }

  submitBtn && submitBtn.addEventListener("click", submitAnswer);
  nextBtn && nextBtn.addEventListener("click", loadQuestion);

  submitBtn && submitBtn.addEventListener("click", submitAnswer);
  nextBtn && nextBtn.addEventListener("click", loadQuestion);
  
  // AI Event Listeners
  getExplanationBtn && getExplanationBtn.addEventListener("click", getExplanation);
  getHintBtn && getHintBtn.addEventListener("click", getHint);
  
  askAiBtn && askAiBtn.addEventListener("click", function() {
    const query = aiInput.value.trim();
    if (query) {
      callAiApi(query, currentQuestion?.id);
      aiInput.value = "";
    }
  });
  
  aiInput && aiInput.addEventListener("keypress", function(e) {
    if (e.key === "Enter") {
      const query = aiInput.value.trim();
      if (query) {
        callAiApi(query, currentQuestion?.id);
        aiInput.value = "";
      }
    }
  });

  // Tính năng Toggle User Menu
  window.toggleUserMenu = function(event) {
    event.stopPropagation(); 
    const menu = document.getElementById('userDropdown');
    if (menu) menu.classList.toggle('show');
  };

  // Đóng menu khi click ra ngoài vùng menu
  document.addEventListener('click', function(event) {
    const menu = document.getElementById('userDropdown');
    const button = document.querySelector('.user-profile-btn');
    
    if (menu && menu.classList.contains('show') && (!button || !button.contains(event.target)) && !menu.contains(event.target)) {
        menu.classList.remove('show');
    }
  });
});