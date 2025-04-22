# Software-Agent
A Demo Project: Manipulating Software APIs with Natural Language.

该项目实现了一个AI代理系统(适用于Web应用)，能够将用户的自然语言指令转换为软件RESTful API调用，Agent使用大型语言模型(OpenAI的GPT-4或Claude)来理解用户意图，并执行相应的软件RESTful API交互操作。

## Project Structure
```
ai_agent/
├── __init__.py
├── main.py
├── run_streamlit.py                
├── config.py
├── .env             
├── agent/
│   ├── __init__.py
│   ├── llm_processor.py   
│   ├── intent_parser.py   
│   └── tool_manager.py    
├── api/
│   ├── __init__.py
│   ├── api_client.py      
│   └── endpoints.py      
├── utils/
│   ├── __init__.py
│   ├── logger.py          
│   └── validators.py      
└── web/
    ├── __init__.py
    ├── app.py             
    ├── handlers.py        
    └── streamlit_app.py   
```

## Install

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 创建一个`.env`文件在项目根目录：

```
# 基础配置
DEBUG=True
LOG_LEVEL=INFO

# 语言模型配置
LLM_PROVIDER=openai  # openai/anthropic
LLM_MODEL=gpt-4
LLM_API_KEY=your_api_key_here
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.7

# API配置
API_BASE_URL=https://api.yoursoftware.com
API_KEY=your_software_api_key_here
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3
API_RETRY_DELAY=2

# Web服务配置
WEB_HOST=0.0.0.0
WEB_PORT=8000
CORS_ORIGINS=*
AUTH_REQUIRED=True
JWT_SECRET=your-super-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600
```

3. 启动后端API服务
```bash
python -m ai_agent.main --debug --log-level=DEBUG
```
4. 启动Streamlit前端
```bash
python run_streamlit.py --port=8501 --api-url=http://localhost:8000/api
```

## Usage

将此Agent应用到其它Software中，需要更新以下组件:
1. `api/endpoints.py` - 更新API端点定义以匹配新的Software API
2. `agent/tool_manager.py` - 自定义工具定义和执行逻辑
3. `.env` - 更新API配置和其他系统设置

然后：

1. 打开Streamlit界面 (http://localhost:8501)
2. 使用 `demo` / `password` 登录
3. 输入自然语言指令
