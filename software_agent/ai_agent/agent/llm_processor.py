import json
import os
from typing import Dict, Any, List, Optional, Union
import requests
from ..config import LLM_CONFIG, BASE_CONFIG
from ..utils.logger import setup_logger


class LLMProcessor:
    """处理与大型语言模型的交互"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or LLM_CONFIG
        self.provider = self.config["provider"]
        self.model = self.config["model"]
        self.api_key = self.config["api_key"]
        self.api_base = self.config["api_base"] or self._get_default_api_base()
        self.max_tokens = self.config["max_tokens"]
        self.temperature = self.config["temperature"]
        self.logger = setup_logger("llm_processor", log_level=BASE_CONFIG["log_level"])

    def _get_default_api_base(self) -> str:
        """获取默认API基础URL"""
        provider_urls = {
            "openai": "https://api.openai.com/v1",
            "anthropic": "https://api.anthropic.com",
            # more...
        }
        return provider_urls.get(self.provider, "")

    def process_input(self, user_input: str, context: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        处理用户输入，返回LLM的响应

        Args:
            user_input: 用户的自然语言输入
            context: 可选的对话上下文

        Returns:
            包含LLM响应的字典
        """
        if self.provider == "openai":
            return self._call_openai_api(user_input, context)
        elif self.provider == "anthropic":
            return self._call_anthropic_api(user_input, context)
        else:
            self.logger.error(f"不支持的LLM提供商: {self.provider}")
            return {"error": f"不支持的LLM提供商: {self.provider}"}

    def _call_openai_api(self, user_input: str, context: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """调用OpenAI API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 准备消息
        messages = []
        if context:
            messages.extend(context)

        # 添加系统提示
        messages.append({
            "role": "system",
            "content": """你是一个AI助手，负责将用户的自然语言指令转换为软件API调用。
            你需要理解用户的意图，并提取出相应的操作、参数和值。
            将响应格式化为JSON，包含以下字段:
            - action: 要执行的操作名称
            - parameters: 操作所需的参数
            - confidence: 你对理解正确的置信度(0-1)
            - clarification_questions: 如果需要更多信息才能正确执行，在这里提出问题
            """
        })

        messages.append({
            "role": "user",
            "content": user_input
        })

        # 请求体
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        try:
            self.logger.debug(f"调用OpenAI API: {self.model}")
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            response_data = response.json()

            # 提取内容
            content = response_data["choices"][0]["message"]["content"]

            # 提取JSON
            try:
                # 尝试直接解析为JSON
                result = json.loads(content)
            except json.JSONDecodeError:
                # 如果失败，尝试从文本中提取JSON部分
                self.logger.warning("直接JSON解析失败，尝试从文本提取")
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    try:
                        result = json.loads(json_str)
                    except json.JSONDecodeError:
                        self.logger.error("无法从响应中提取有效JSON")
                        result = {"error": "无法解析语言模型响应", "raw_response": content}
                else:
                    result = {"error": "响应中没有找到JSON格式", "raw_response": content}

            return result

        except requests.exceptions.RequestException as e:
            self.logger.error(f"API请求失败: {str(e)}")
            return {"error": f"API请求失败: {str(e)}"}

    def _call_anthropic_api(self, user_input: str, context: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """调用Anthropic API (Claude)"""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        # 准备消息
        system_prompt = """你是一个AI助手，负责将用户的自然语言指令转换为软件API调用。
        你需要理解用户的意图，并提取出相应的操作、参数和值。
        将响应格式化为JSON，包含以下字段:
        - action: 要执行的操作名称
        - parameters: 操作所需的参数
        - confidence: 你对理解正确的置信度(0-1)
        - clarification_questions: 如果需要更多信息才能正确执行，在这里提出问题
        """

        messages = []
        if context:
            for msg in context:
                role = msg["role"]
                if role == "user":
                    messages.append({"role": "user", "content": msg["content"]})
                elif role == "assistant":
                    messages.append({"role": "assistant", "content": msg["content"]})

        # 请求体
        data = {
            "model": self.model,
            "system": system_prompt,
            "messages": messages + [{"role": "user", "content": user_input}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }

        try:
            self.logger.debug(f"调用Anthropic API: {self.model}")
            response = requests.post(
                f"{self.api_base}/messages",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            response_data = response.json()

            # 提取内容
            content = response_data["content"][0]["text"]

            # 提取JSON
            try:
                # 尝试直接解析为JSON
                result = json.loads(content)
            except json.JSONDecodeError:
                # 如果失败，尝试从文本中提取JSON部分
                self.logger.warning("直接JSON解析失败，尝试从文本提取")
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    try:
                        result = json.loads(json_str)
                    except json.JSONDecodeError:
                        self.logger.error("无法从响应中提取有效JSON")
                        result = {"error": "无法解析语言模型响应", "raw_response": content}
                else:
                    result = {"error": "响应中没有找到JSON格式", "raw_response": content}

            return result

        except requests.exceptions.RequestException as e:
            self.logger.error(f"API请求失败: {str(e)}")
            return {"error": f"API请求失败: {str(e)}"}