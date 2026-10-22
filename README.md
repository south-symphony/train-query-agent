# 12306车次查询智能体
基于 MCP 协议与智谱AI构建的火车票查询 AI 智能体，支持自然语言交互、实时余票查询、多轮对话记忆与网页端可视化界面。

## ✨ 核心功能
- 🗣️ 自然语言对话：基于智谱 GLM-4-Flash 免费大模型，日常口语即可完成查询
- 🛠️ 工具调用能力：遵循 MCP 协议标准封装工具，智能体自主判断并调用 12306 官方接口
- 🧠 多轮对话记忆：自动保留对话上下文，复用用户提到的出发地、目的地等信息
- 🌐 真实接口对接：直连 12306 官方余票接口，车次、时刻、余票状态实时更新
- 🖥️ 网页端界面：美观的可视化聊天窗口，启动后自动打开浏览器
- 🔐 密钥安全管理：API 密钥通过 `.env` 文件独立存储，符合代码安全规范

## 🛠️ 技术栈
- 大语言模型：智谱AI GLM-4-Flash
- 智能体协议：MCP (Model Context Protocol)
- 开发语言：Python 3.10+
- Web 框架：Flask
- 前端：原生 HTML + CSS + JavaScript
- HTTP 客户端：httpx

## 📋 环境要求
- Python 3.10+
- Windows、macOS 或 Linux
- 一个智谱AI API Key（GLM-4-Flash 免费模型即可）

仓库中已经包含：

- `mcp_server/` MCP 协议车次查询工具服务
- `agent/` 智能体核心逻辑 + 多轮对话记忆模块
- `web/` 网页端聊天界面与后端服务
- `requirements.txt` Python 依赖配置文件

因此普通使用者只需安装 Python 依赖并配置 API 密钥即可启动。

## 🚀 快速开始
### 1. 安装依赖
Windows 系统在项目根目录依次执行：
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate

# 安装所有依赖
pip install -r requirements.txt

### 2. 配置密钥

在项目根目录创建 `.env` 文件，填入：

ZHIPUAI_API_KEY=你的智谱AI API密钥

### 3. 三种启动模式

# 模式一：命令行模式

适合开发者调试、快速测试，无需网页界面。

1. 确保已完成依赖安装
2. 将 `.env.example` 重命名为为 `.env` ，打开 `.env` 文件，填入你的智谱 AI API 密钥并保存
3. 在项目根目录执行：

```
python agent\agent_core.py
```

3. 在控制台直接输入文字对话即可，输入 `退出` 结束程序。

---

# 模式二：网页界面模式（推荐）

可视化聊天界面，普通用户推荐使用此模式。

1. 确保已完成依赖安装
2. 将 `.env.example` 重命名为为 `.env` ，打开 `.env` 文件，填入你的智谱 AI API 密钥并保存
3. 在项目根目录执行：

```
python web\app.py
```

3. 程序启动后会自动打开默认浏览器，进入聊天界面
4. 关闭命令行窗口即可停止服务。

---

# 模式三：发行版可执行模式

无需安装 Python 环境与依赖，下载即可运行。

1. 从 GitHub Release 页面下载发行版压缩包并解压
2. 将解压目录中的 `.env.example` 重命名为 `.env`
3. 打开 `.env` 文件，填入你的智谱 AI API 密钥并保存
4. 双击 `12306-Train-Agent.exe` 启动程序
5. 程序会自动打开浏览器进入聊天界面，关闭黑色命令行窗口即可停止。

## 📂 项目目录结构

train-query-agent/
├── .env                # 环境变量（存放API密钥）
├── .env.example        # 环境变量模板
├── .gitignore          # Git 忽略配置
├── requirements.txt    # 依赖包列表
├── README.md
├── mcp_server/         # MCP 服务端 - 12306 查询工具封装
│   ├── __init__.py
│   └── server.py
├── agent/              # 智能体核心模块
│   ├── __init__.py
│   ├── memory.py       # 多轮对话记忆管理
│   └── agent_core.py   # 大模型对接 + 工具调用逻辑
└── web/                # 网页前端服务
    ├── app.py
    └── templates/
        └── index.html
