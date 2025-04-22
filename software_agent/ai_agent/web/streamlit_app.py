import streamlit as st
import requests
import json
import uuid
import datetime
import os
from typing import Dict, Any, List, Optional

# 配置
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")
DEFAULT_HEADERS = {
    "Content-Type": "application/json"
}


class AIAgentClient:
    """AI Agent API客户端"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        # 不再需要令牌

    def create_conversation(self) -> Dict[str, Any]:
        """创建新对话"""
        response = requests.post(
            f"{self.base_url}/conversations",
            headers=DEFAULT_HEADERS
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "message": f"创建对话失败 ({response.status_code}): {response.text}"}

    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """获取对话历史"""
        response = requests.get(
            f"{self.base_url}/conversations/{conversation_id}",
            headers=DEFAULT_HEADERS
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "message": f"获取对话失败 ({response.status_code}): {response.text}"}

    def process_message(self, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """处理用户消息"""
        payload = {
            "message": message
        }
        if conversation_id:
            payload["conversation_id"] = conversation_id

        response = requests.post(
            f"{self.base_url}/process",
            headers=DEFAULT_HEADERS,
            json=payload
        )
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "message": f"处理消息失败 ({response.status_code}): {response.text}"}


# 初始化会话状态
def init_session_state():
    """初始化Streamlit会话状态"""
    if 'client' not in st.session_state:
        st.session_state.client = AIAgentClient()

    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = None
        # 自动创建一个新对话
        create_new_conversation()

    if 'messages' not in st.session_state:
        st.session_state.messages = []


# 发送消息处理
def handle_send_message(message: str):
    """处理发送消息"""
    if not message.strip():
        return

    # 添加用户消息到界面
    st.session_state.messages.append({"role": "user", "content": message})

    # 处理消息
    result = st.session_state.client.process_message(message, st.session_state.conversation_id)

    if result.get("success", False):
        # 添加助手回复到界面
        assistant_message = result.get("message", "我无法理解您的请求。")
        st.session_state.messages.append({"role": "assistant", "content": assistant_message})
    else:
        # 添加错误消息
        error_msg = result.get("message", "处理消息时发生错误")
        st.session_state.messages.append({"role": "assistant", "content": f"错误: {error_msg}"})


# 创建新对话
def create_new_conversation():
    """创建新对话"""
    result = st.session_state.client.create_conversation()
    if result.get("success", False):
        st.session_state.conversation_id = result["data"]["conversation_id"]
        st.session_state.messages = []
        return True
    return False


# 主应用
def main():
    """主应用函数"""
    st.set_page_config(
        page_title="RESTful API Agent",
        page_icon="🤖",
        layout="wide"
    )

    # 初始化会话状态
    init_session_state()

    # 侧边栏
    with st.sidebar:
        st.title("🤖 RESTful API Agent")

        if st.button("开始新对话", key="new_conversation"):
            if create_new_conversation():
                st.success("已创建新对话！")
                st.rerun()
            else:
                st.error("创建新对话失败。")

    # 主体内容
    col1, col2 = st.columns([2, 1])

    with col1:
        st.title("AI Agent 对话")

        # 显示对话框
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.messages:
                role = msg["role"]
                content = msg["content"]

                if role == "user":
                    st.chat_message("user", avatar="👤").write(content)
                else:
                    st.chat_message("assistant", avatar="🤖").write(content)

        # 消息输入框
        user_input = st.chat_input("输入自然语言指令...")
        if user_input:
            handle_send_message(user_input)
            st.rerun()

    with col2:
        st.subheader("系统信息")
        st.info(f"当前对话ID: {st.session_state.conversation_id}")

        # 当前时间
        now = datetime.datetime.now()
        st.text(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # 操作提示
        st.subheader("使用提示")
        st.markdown("""
        **示例指令:**
        - "查看所有项目列表"
        - "创建一个名为'营销分析'的新项目"
        - "获取项目ID为123的详细信息"
        - "为项目456上传销售数据文件"
        - "运行项目789的数据分析"
        - "查看系统状态"
        """)


if __name__ == "__main__":
    main()
