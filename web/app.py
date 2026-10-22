"""
Flask Web服务 - 提供网页聊天界面
兼容源码运行与exe打包，自动适配路径
"""
import os
import sys
import time
import threading
import webbrowser
from flask import Flask, render_template, request, jsonify

# 路径适配：区分源码运行和exe打包运行
if getattr(sys, 'frozen', False):
    # exe打包模式：所有文件都解压在临时目录 _MEIPASS
    BASE_PATH = sys._MEIPASS
else:
    # 源码运行模式：以当前文件所在目录为基准
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# 把所有模块所在的根目录加入系统路径
PROJECT_ROOT = os.path.dirname(BASE_PATH) if not getattr(sys, 'frozen', False) else BASE_PATH
sys.path.insert(0, PROJECT_ROOT)

from agent.agent_core import TrainQueryAgent

# 初始化Flask，指定模板路径
app = Flask(__name__, template_folder=os.path.join(BASE_PATH, 'templates'))

# 全局智能体实例
agent = None


def get_agent():
    """获取智能体单例"""
    global agent
    if agent is None:
        agent = TrainQueryAgent()
    return agent


def open_browser():
    """延迟打开浏览器"""
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:5000")


@app.route('/')
def index():
    """首页 - 聊天界面"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """对话接口"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({"success": False, "error": "消息不能为空"})
        
        agent = get_agent()
        reply = agent.chat(user_message)
        
        return jsonify({
            "success": True,
            "reply": reply
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/clear', methods=['POST'])
def clear():
    """清空对话记忆"""
    try:
        agent = get_agent()
        agent.clear_memory()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == '__main__':
    print("=" * 50)
    print("🚄 12306智能查询助手 启动中...")
    print("📱 浏览器访问地址: http://127.0.0.1:5000")
    print("❌ 关闭此窗口即可停止服务")
    print("=" * 50)
    
    # 自动打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    
    # 启动服务
    app.run(debug=False, host='0.0.0.0', port=5000)
