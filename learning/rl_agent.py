import random
import json
from typing import Dict, List, Tuple

class ReinforcementLearningAgent:
    def __init__(self, profile):
        self.profile = profile
        # Các hằng số RL theo báo cáo NCKH
        self.ALPHA = 0.1  # Learning rate
        self.GAMMA = 0.9  # Discount factor
        self.EPSILON = 0.1 # Exploration rate
        
        # Danh sách hành động khả thi [cite: 359]
        self.ACTIONS = [
            "Recommend_Exercise", 
            "Recommend_Material", 
            "Virtual_Tutor", 
            "Review_Weak_Area"
        ]
        
        # Load bảng Q từ JSONField của UserProfile [cite: 343, 393]
        if isinstance(self.profile.q_policy, str):
            self.q_table = json.loads(self.profile.q_policy)
        else:
            self.q_table = self.profile.q_policy or {}

    def _state_key(self) -> str:
        """Định danh trạng thái S (4 chiều) [cite: 357]"""
        level = self.profile.level
        # Rời rạc hóa số lượng vùng yếu
        weak_count = min(2, len(self.profile.weak_areas or []))
        # Rời rạc hóa độ chính xác (Accuracy) và hoàn thành (Completion) [cite: 357]
        # Giả định các giá trị này được lưu trong profile
        acc = "High" if getattr(self.profile, 'accuracy', 0) > 0.8 else "Low"
        comp = "Done" if getattr(self.profile, 'completion_rate', 0) > 0.7 else "Pending"
        
        return f"L{level}|W{weak_count}|A{acc}|C{comp}"

    def select_action(self) -> str:
        """Chọn hành động tối ưu dựa trên chính sách epsilon-greedy [cite: 446]"""
        state = self._state_key()
        
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.ACTIONS}
            
        if random.random() < self.EPSILON:
            return random.choice(self.ACTIONS)
        
        # Chọn hành động có giá trị Q cao nhất
        state_actions = self.q_table[state]
        return max(state_actions, key=state_actions.get)

    def calculate_reward(self, is_correct: bool, sub_category: str) -> float:
        """Hàm phần thưởng khớp 100% với báo cáo [cite: 360, 362, 363, 364]"""
        # R_base
        reward = 5.0 if is_correct else -5.0
        
        is_weak = sub_category in (self.profile.weak_areas or [])
        
        if is_correct:
            # Khuyến khích vượt khó: Thưởng +8 khi đúng ở vùng yếu [cite: 362]
            if is_weak:
                reward = 8.0
            # Động lực tiến bộ: R = R_base + (Level * 2) [cite: 364]
            reward += (self.profile.level * 2)
        else:
            # Phạt cảnh báo: Trừ -13 khi sai ở vùng yếu [cite: 363]
            if is_weak:
                reward = -13.0
                
        return float(reward)

    def update_q_value(self, state: str, action: str, reward: float, next_state: str):
        """Cập nhật giá trị Q theo phương trình Bellman [cite: 448]"""
        if state not in self.q_table: self.q_table[state] = {a: 0.0 for a in self.ACTIONS}
        if next_state not in self.q_table: self.q_table[next_state] = {a: 0.0 for a in self.ACTIONS}
        
        old_value = self.q_table[state][action]
        next_max = max(self.q_table[next_state].values())
        
        # Q(s,a) = (1-α)Q(s,a) + α(R + γ*maxQ(s',a'))
        new_value = (1 - self.ALPHA) * old_value + self.ALPHA * (reward + self.GAMMA * next_max)
        self.q_table[state][action] = round(new_value, 3)
        
        # Lưu lại vào profile
        self.profile.q_policy = self.q_table
        self.profile.save()

    def update_mastery(self, category: str, sub_category: str, is_correct: bool):
        """Cập nhật Knowledge Tracing cho đúng kỹ năng (Grammar/Listening/Vocab)"""
        
        # 1. Tự động xác định tên trường cần cập nhật (grammar_mastery hoặc listening_mastery)
        # Nếu category là 'listening', attr_name sẽ là 'listening_mastery'
        attr_name = f"{category.lower()}_mastery"
        
        # Lấy giá trị hiện tại của kỹ năng đó, mặc định 0.1 nếu chưa có
        current_m = getattr(self.profile, attr_name, 0.1)
        
        # 2. Tính toán Mastery mới theo logic báo cáo (+0.05 hoặc -0.07)
        delta = 0.05 if is_correct else -0.07 
        new_mastery = max(0.0, min(1.0, current_m + delta))
        
        # 3. Ghi đè giá trị mới vào đúng kỹ năng đó trong Profile
        setattr(self.profile, attr_name, round(new_mastery, 2))
        
        # 4. Quản lý vùng yếu (Weak Areas)
        wa = set(self.profile.weak_areas or [])
        if new_mastery < 0.4:
            wa.add(sub_category)
        else:
            wa.discard(sub_category)
            
        self.profile.weak_areas = list(wa)
        self.profile.save()