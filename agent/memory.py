import json
import os
from datetime import datetime

MEMORY_FILE = "user_memory.json"

class MemoryManager:
    def __init__(self):
        self.memory_file = MEMORY_FILE
        self.load_memory()

    def load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except:
                self.data = {"behaviors": [], "rules": [], "tasks": []}
        else:
            self.data = {"behaviors": [], "rules": [], "tasks": []}

    def save_memory(self):
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def add_behavior(self, context, action, timestamp=None):
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        entry = {
            "timestamp": timestamp,
            "context": context, # e.g., "Opened YouTube"
            "action": action    # e.g., "AI suggested opening music"
        }
        self.data["behaviors"].append(entry)
        self.save_memory()
        return "Memory saved."

    def add_rule(self, rule_content):
        """
        Thêm một luật mới mà AI tự học được hoặc người dùng dạy.
        Ví dụ: 'Khi mở Chrome vào buổi sáng, hãy mở sẵn trang tin tức.'
        """
        entry = {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "content": rule_content
        }
        self.data["rules"].append(entry)
        self.save_memory()
        return "Rule learned and saved."

    def get_all_rules(self):
        return [r["content"] for r in self.data["rules"]]

    def get_recent_behaviors(self, limit=5):
        return self.data["behaviors"][-limit:]

# Global instance
memory_manager = MemoryManager()

def learn_new_rule(rule_content):
    return memory_manager.add_rule(rule_content)

def get_learned_rules():
    return memory_manager.get_all_rules()
