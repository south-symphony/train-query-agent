"""
多轮对话记忆模块
管理对话历史，支持上下文记忆
"""
from typing import List, Dict


class ConversationMemory:
    def __init__(self, max_history: int = 20):
        """
        初始化记忆
        :param max_history: 最大保留的对话轮数（每条包含user+assistant算一轮）
        """
        self.history: List[Dict[str, str]] = []
        self.max_history = max_history
    
    def add_user_message(self, content: str):
        """添加用户消息"""
        self.history.append({"role": "user", "content": content})
        self._trim_history()
    
    def add_assistant_message(self, content: str):
        """添加助手回复"""
        self.history.append({"role": "assistant", "content": content})
        self._trim_history()
    
    def add_system_message(self, content: str):
        """添加系统提示词（只在最前面加一次）"""
        if not self.history or self.history[0]["role"] != "system":
            self.history.insert(0, {"role": "system", "content": content})
    
    def get_messages(self) -> List[Dict[str, str]]:
        """获取完整对话历史"""
        return self.history.copy()
    
    def clear(self):
        """清空对话历史"""
        self.history = []
    
    def _trim_history(self):
        """裁剪历史，保留system和最近的对话"""
        # 保留system消息
        has_system = self.history and self.history[0]["role"] == "system"
        system_msg = self.history[0] if has_system else None
        
        # 普通对话消息
        normal_msgs = [m for m in self.history if m["role"] != "system"]
        
        # 限制数量
        if len(normal_msgs) > self.max_history:
            normal_msgs = normal_msgs[-self.max_history:]
        
        # 重新组合
        self.history = []
        if system_msg:
            self.history.append(system_msg)
        self.history.extend(normal_msgs)
