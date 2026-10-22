"""
智能体核心 - 整合智谱AI + MCP工具调用 + 多轮记忆
车次查询结果直出，保证完整不省略
"""
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from zhipuai import ZhipuAI

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.memory import ConversationMemory

# 加载环境变量
load_dotenv()


class TrainQueryAgent:
    def __init__(self):
        api_key = os.getenv("ZHIPUAI_API_KEY")
        if not api_key:
            raise ValueError("请在.env文件中配置 ZHIPUAI_API_KEY")
        
        self.client = ZhipuAI(api_key=api_key)
        self.model = "glm-4-flash"
        
        # 初始化记忆
        self.memory = ConversationMemory(max_history=10)
        self._refresh_system_prompt()
        
        # 工具定义
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "query_train_tickets",
                    "description": "查询两个城市之间的火车车次、余票、出发到达时间等信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "from_station": {"type": "string", "description": "出发城市中文名称"},
                            "to_station": {"type": "string", "description": "到达城市中文名称"},
                            "date": {"type": "string", "description": "出发日期，格式YYYY-MM-DD"}
                        },
                        "required": ["from_station", "to_station", "date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_supported_stations",
                    "description": "获取支持查询的热门车站列表",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]
    
    def _refresh_system_prompt(self):
        today = datetime.now().strftime("%Y-%m-%d")
        system_prompt = f"""
你是一个专业的火车票查询助手，名字叫「小铁」。
今天的日期是：{today}

你的能力：
1. 自然对话：友好回应用户，理解出行需求
2. 查询车次：调用 query_train_tickets 工具查询车次余票
3. 查询车站：调用 get_supported_stations 工具查看支持的车站

规则：
- 用户说"明天/后天"时，根据今天的日期推算准确日期
- 信息不全时主动询问用户缺少的内容
- 回答亲切自然，像真人客服一样
        """.strip()
        
        self.memory.history = [m for m in self.memory.history if m["role"] != "system"]
        self.memory.history.insert(0, {"role": "system", "content": system_prompt})
    
    def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """执行工具调用"""
        from mcp_server.server import query_train_tickets, get_supported_stations
        
        try:
            if tool_name == "query_train_tickets":
                return query_train_tickets(**arguments)
            elif tool_name == "get_supported_stations":
                return get_supported_stations()
            else:
                return f"未知工具：{tool_name}"
        except Exception as e:
            return f"工具执行出错：{str(e)}"
    
    def chat(self, user_input: str) -> str:
        """与智能体对话"""
        self._refresh_system_prompt()
        self.memory.add_user_message(user_input)
        
        # 第一次调用大模型
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.memory.get_messages(),
            tools=self.tools,
            tool_choice="auto",
            temperature=0.7,
            timeout=30
        )
        
        message = response.choices[0].message
        
        # 判断是否需要调用工具
        if hasattr(message, 'tool_calls') and message.tool_calls:
            # 目前只有一个工具调用，取第一个即可
            tool_call = message.tool_calls[0]
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except:
                arguments = {}
            
            # 执行工具，拿到完整结果
            tool_result = self._execute_tool(tool_name, arguments)
            
            # 如果是车次查询，直接返回完整结果，不经过模型二次改写，保证100%完整
            if tool_name == "query_train_tickets":
                final_answer = tool_result
            else:
                # 其他工具调用走正常流程
                assistant_msg = {
                    "role": "assistant",
                    "content": message.content if message.content else "",
                    "tool_calls": [{
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": tool_call.function.arguments
                        }
                    }]
                }
                tool_msg = {"role": "tool", "tool_call_id": tool_call.id, "content": tool_result}
                
                messages = self.memory.get_messages()
                messages.append(assistant_msg)
                messages.append(tool_msg)
                
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7,
                    timeout=30
                )
                final_answer = second_response.choices[0].message.content
        else:
            final_answer = message.content
        
        self.memory.add_assistant_message(final_answer)
        return final_answer
    
    def clear_memory(self):
        """清空对话记忆"""
        self.memory.clear()
        self._refresh_system_prompt()


# 命令行测试入口
if __name__ == "__main__":
    agent = TrainQueryAgent()
    print("智能体已启动，输入 '退出' 结束对话\n")
    
    while True:
        user_input = input("你：")
        if user_input in ["退出", "exit", "quit"]:
            break
        
        reply = agent.chat(user_input)
        print(f"小铁：{reply}\n")
