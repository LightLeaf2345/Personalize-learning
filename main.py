import json
import random
import os
import sys
import pyodbc
from datetime import datetime
from typing import Dict, List, Tuple
from playsound import playsound
from dataclasses import dataclass, field
from environ import Env
import os

env = Env()
Env.read_env()
# ============================================
# 1. DATABASE MANAGER
# ============================================
class DatabaseManager:
    def __init__(self):
        self.conn_string = (
            f"DRIVER={{{env('DB_DRIVER')}}};"
            f"SERVER={env('DB_HOST')};"
            f"DATABASE={env('DB_NAME')};"
            f"UID={env('DB_USER')};"
            f"PWD={env('DB_PASSWORD')};"
            "TrustServerCertificate=yes;"
        )

    def get_connection(self):
        return pyodbc.connect(self.conn_string)

    def load_user(self, user_id: str) -> dict:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT current_level, vocabulary_size, weak_areas_json, 
                           vocabulary_bank_json, learning_history_json 
                    FROM UserProgress WHERE user_id = ?
                """, (user_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        'level': row[0], 'vocabulary_size': row[1],
                        'weak_areas': json.loads(row[2]) if row[2] else [],
                        'vocabulary_bank': json.loads(row[3]) if row[3] else {},
                        'learning_history': json.loads(row[4]) if row[4] else []
                    }
                return None
        except Exception as e:
            print(f"[Lỗi DB Load User]: {e}")
            return None

    def save_user(self, profile):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                weak_areas_str = json.dumps(profile.weak_areas)
                vocab_bank_str = json.dumps(profile.vocabulary_bank)
                history_str = json.dumps(profile.learning_history)
                
                sql = """
                IF EXISTS (SELECT 1 FROM UserProgress WHERE user_id = ?)
                    UPDATE UserProgress 
                    SET current_level = ?, vocabulary_size = ?, 
                        weak_areas_json = ?, vocabulary_bank_json = ?, learning_history_json = ?, last_updated = GETDATE()
                    WHERE user_id = ?
                ELSE
                    INSERT INTO UserProgress (user_id, current_level, vocabulary_size, weak_areas_json, vocabulary_bank_json, learning_history_json) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                cursor.execute(sql, profile.user_id, profile.level, profile.vocabulary_size, weak_areas_str, vocab_bank_str, history_str, profile.user_id,
                               profile.user_id, profile.level, profile.vocabulary_size, weak_areas_str, vocab_bank_str, history_str)
                conn.commit()
                return True
        except Exception as e:
            print(f"[Lỗi DB Save User]: {e}")
            return False

    def get_random_vocabulary(self, level: str) -> dict:
        """Lấy 1 từ vựng ngẫu nhiên từ DB theo level"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT TOP 1 word, meaning, example FROM AppVocabulary WHERE level = ? ORDER BY NEWID()", (level,))
                row = cursor.fetchone()
                if row:
                    return {"word": row[0], "meaning": row[1], "example": row[2]}
        except Exception as e:
            print(f"[Lỗi kéo Từ vựng]: {e}")
        return {"word": "database", "meaning": "a structured set of data", "example": "I connected to the database."}

    def get_random_grammar(self) -> dict:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT MIN(grammar_id), MAX(grammar_id) FROM AppGrammar")
                min_id, max_id = cursor.fetchone()
                
                if min_id is None:
                    raise Exception("Bảng Grammar đang trống!")
                
                random_id = random.randint(min_id, max_id)
                
                cursor.execute("""
                    SELECT TOP 1 sentence, options_json, correct_answer, explanation 
                    FROM AppGrammar 
                    WHERE grammar_id >= ?
                """, (random_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "sentence": row[0], 
                        "options": json.loads(row[1]), 
                        "correct": row[2], 
                        "explanation": row[3]
                    }
        except Exception as e:
            print(f"[Lỗi kéo Ngữ pháp]: {e}")
            
        return None
    

    def get_random_listening(self) -> dict:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT TOP 1 
                        ts.title, ts.media_url, 
                        q.question_text, q.correct_answer, q.explanation
                    FROM Test_Sections ts
                    JOIN Question_Groups qg ON ts.section_id = qg.section_id
                    JOIN Questions q ON qg.group_id = q.group_id
                    WHERE ts.skill_type = 'Listening' AND ts.media_url IS NOT NULL
                    ORDER BY NEWID()
                """
                cursor.execute(query)
                row = cursor.fetchone()
                if row:
                    return {
                        "title": row[0],
                        "media_url": row[1],
                        "question": row[2],
                        "correct": row[3],
                        "explanation": row[4]
                    }
        except Exception as e:
            print(f"[Lỗi kéo Listening]: {e}")
        return None

# ============================================
# 2. USER PROFILE
# ============================================
@dataclass
class UserProfile:
    user_id: str
    level: str = "beginner"
    vocabulary_size: int = 0
    weak_areas: List[str] = field(default_factory=list)
    learning_history: List[Dict] = field(default_factory=list)
    vocabulary_bank: Dict[str, int] = field(default_factory=dict)

# ============================================
# 3. MAPPING MANAGERS  
# ============================================
class VocabularyManager:
    def __init__(self, db: DatabaseManager):
        self.db = db 
    
    def get_word_for_level(self, level: str) -> Dict:
        return self.db.get_random_vocabulary(level)

class GrammarPractice:
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    def generate_exercise(self) -> Dict:
        return self.db.get_random_grammar()
    
    def check_answer(self, exercise: Dict, user_answer: str) -> Tuple[bool, str]:
        # Tạo sẵn một chuỗi chứa lời giải thích
        explanation_text = f"\n💡 Giải thích: {exercise['explanation']}"
        
        if exercise and user_answer.strip().lower() == exercise['correct'].lower():
            return True, "✅ Chính xác! Rất xuất sắc!" + explanation_text
            
        return False, f"❌ Tiếc quá, sai rồi. Đáp án đúng là: {exercise['correct']}" + explanation_text

# ============================================
# 4. MAIN LEARNING APP
# ============================================
class PersonalizedEnglishLearningApp:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.user_profile = UserProfile(user_id=user_id)
        
        self.db = DatabaseManager() 
        
        self.vocab_manager = VocabularyManager(self.db)
        self.grammar_practice = GrammarPractice(self.db)
        
        self.load_user_data()
    
    def load_user_data(self):
        data = self.db.load_user(self.user_id)
        if data:
            self.user_profile.level = data.get('level', 'beginner')
            self.user_profile.vocabulary_size = data.get('vocabulary_size', 0)
            self.user_profile.weak_areas = data.get('weak_areas', [])
            self.user_profile.vocabulary_bank = data.get('vocabulary_bank', {})
            self.user_profile.learning_history = data.get('learning_history', [])
            print(f"✅ Loaded data from SQL Server for user: {self.user_id}")
        else:
            print(f"🆕 Creating new profile in SQL Server for: {self.user_id}")
    
    def save_user_data(self):
        if self.db.save_user(self.user_profile):
            print("💾 Progress saved to Database!")

    def practice_vocabulary(self):
        print("\n" + "="*50 + "\n📚 VOCABULARY PRACTICE\n" + "="*50)
        word_data = self.vocab_manager.get_word_for_level(self.user_profile.level)
        print(f"\n🎯 New Word: {word_data['word'].upper()}\n📖 Meaning: {word_data['meaning']}\n📝 Example: {word_data['example']}")
        
        input("\nPress Enter when you're ready to continue...")
        user_answer = input(f"\n❓ Quick Quiz: What does '{word_data['word']}' mean?\nYour answer: ")
        
        if word_data['word'] not in self.user_profile.vocabulary_bank:
            self.user_profile.vocabulary_bank[word_data['word']] = 1
            self.user_profile.vocabulary_size += 1
            print(f"✨ Added '{word_data['word']}' to your vocabulary!")
        else:
            self.user_profile.vocabulary_bank[word_data['word']] += 1
            print(f"🔁 Reviewed '{word_data['word']}' (review count: {self.user_profile.vocabulary_bank[word_data['word']]})")

    def practice_grammar(self):
        print("\n" + "="*50 + "\n📝 GRAMMAR PRACTICE\n" + "="*50)
        exercise = self.grammar_practice.generate_exercise()
        print(f"\n➡️  {exercise['sentence']}\nOptions:")
        for i, option in enumerate(exercise['options'], 1): print(f"  {i}. {option}")
        
        user_answer = input("\nEnter the NUMBER or the WORD: ").strip()
        if user_answer.isdigit() and 0 <= int(user_answer) - 1 < len(exercise['options']):
            user_answer = exercise['options'][int(user_answer) - 1]
            
        is_correct, feedback = self.grammar_practice.check_answer(exercise, user_answer)
        print(f"\n{feedback}")
        
        if not is_correct:
            if "___" in exercise['sentence'] and "fill_in_blank" not in self.user_profile.weak_areas:
                self.user_profile.weak_areas.append("fill_in_blank")

    def practice_listening(self):
        print("\n" + "="*50 + "\n🎧 LISTENING PRACTICE\n" + "="*50)
        
        CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) 
        ROOT_AUDIO_FOLDER = os.path.join(CURRENT_DIR, "listening")
        
        exercise = self.db.get_random_listening()
        
        if not exercise:
            print("❌ Chưa có dữ liệu Listening trong Database hoặc bị lỗi.")
            return

        print(f"\n📢 Bài nghe: {exercise['title']}")
        
        audio_path = None
        target_filename = exercise['media_url']
        
        for root, dirs, files in os.walk(ROOT_AUDIO_FOLDER):
            if target_filename in files:
                audio_path = os.path.join(root, target_filename) 
                break
        
        if audio_path and os.path.exists(audio_path):
            print(f"📁 Đã tìm thấy file tại: {audio_path}")
            print("▶️ Đang phát bài nghe... (Vui lòng lắng nghe)")
            playsound(audio_path, block=False) 
        else:
            print(f"⚠️ [LỖI]: Không tìm thấy file '{target_filename}'")
            print(f"👉 Hệ thống đã quét ngóc ngách trong thư mục '{ROOT_AUDIO_FOLDER}' nhưng không có.")
            print("💡 Hãy kiểm tra lại xem file mp3 đã được bỏ vào đó chưa, và TÊN FILE trong SQL có khớp 100% với tên thật không nhé.")

        # Hiển thị câu hỏi
        print(f"\n📝 Câu hỏi: {exercise['question']}")
        user_answer = input("\nEnter your answer: ").strip()
        
        # Chấm điểm
        if user_answer.lower() == exercise['correct'].lower():
            print("\n✅ Correct! Well done!")
        else:
            print(f"\n❌ Incorrect. Right answer: {exercise['correct']}")
            print(f"💡 Explanation: {exercise['explanation']}")           

    def show_progress(self):
        print("\n" + "="*50 + "\n📊 YOUR PROGRESS REPORT\n" + "="*50)
        print(f"👤 User: {self.user_id}\n📈 Level: {self.user_profile.level.upper()}\n📚 Words Learned: {self.user_profile.vocabulary_size}")
        print(f"⚠️  Areas to Improve: {', '.join(self.user_profile.weak_areas) if self.user_profile.weak_areas else 'None'}")

    def run_daily_session(self):
        print("\n" + "="*50 + f"\n🎓 WELCOME TO ENGLISH LEARNING, {self.user_id.upper()}!\n" + "="*50)
        self.practice_vocabulary()
        self.practice_grammar()
        self.save_user_data()
        self.show_progress()
        print("\n" + "="*50 + "\n✅ DAILY SESSION COMPLETED!\n" + "="*50)

# ============================================
# 5. MENU CHÍNH
# ============================================
def main():
    print("\n" + "✨" * 25 + "\n    PERSONALIZED ENGLISH LEARNING SYSTEM\n" + "✨" * 25)
    
    user_input = input("\nEnter user ID or 'new': ").strip()
    if user_input.lower() == 'new':
        user_id = input("Choose a username: ").strip() or f"student_{random.randint(1000, 9999)}"
        print(f"Generated username: {user_id}")
    else:
        user_id = user_input
    
    app = PersonalizedEnglishLearningApp(user_id)
    
    while True:
        print("\n" + "="*50 + "\n📋 MAIN MENU\n" + "="*50)
        print("1. 📚 Start Daily Learning Session")
        print("2. 📊 View My Progress")
        print("3. 🆕 Practice Vocabulary Only")
        print("4. ✏️  Practice Grammar Only")
        print("5. 🎧 Practice Listening Only")  
        print("6. 💾 Save Progress")
        print("7. 🚪 Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == '1': app.run_daily_session()
        elif choice == '2': app.show_progress()
        elif choice == '3':
            app.practice_vocabulary()
            app.save_user_data()
        elif choice == '4':
            app.practice_grammar()
            app.save_user_data()
        elif choice == '5':                  
            app.practice_listening()
            app.save_user_data()
        elif choice == '6': app.save_user_data()
        elif choice == '7':
            print("\n👋 Thank you for learning! Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter a number from 1 to 7.")
        
        input("\nPress Enter to continue to the menu...")

if __name__ == "__main__":
    main()